"""Accounts: sign up / sign in, profile, search history and saved products."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg.types.json import Jsonb

from src.api.auth import (
    _DUMMY_HASH,
    bearer_token,
    create_session,
    current_user,
    delete_session,
    hash_password,
    login_allowed,
    verify_password,
)
from src.api.db import get_repo, query, query_one
from src.api.schemas import (
    AuthResponse,
    HistoryItem,
    LoginBody,
    Me,
    Profile,
    RegisterBody,
    SavedProduct,
)
from src.recommender.config import GOAL_LABELS

router = APIRouter()

HISTORY_KEEP = 200  # newest searches kept per user; older ones are dropped

PROFILE_COLUMNS = "skin_type, goals, avoided_ingredients, fragrance_free, max_price, preferred_category"


# ---------- helpers ----------

def load_profile(repo, user_id: int) -> Profile:
    row = query_one(repo, f"SELECT {PROFILE_COLUMNS} FROM user_profiles WHERE user_id = %s", (user_id,))
    if row is None:
        return Profile()
    row["max_price"] = float(row["max_price"]) if row["max_price"] is not None else None
    return Profile(**row)


def me(repo, user) -> Me:
    return Me(**user, profile=load_profile(repo, user["user_id"]))


def describe_recommend(params: dict) -> str:
    """A short readable line for a goals + filters search, e.g. "Hydration · Moisturizers · under $50"."""
    parts = [", ".join(GOAL_LABELS.get(g, g) for g in params.get("goals") or []) or "Any goal"]
    where = params.get("subcategory") or params.get("category")
    if where:
        parts.append(where)
    if params.get("max_price"):
        parts.append(f"under ${params['max_price']:g}")
    if params.get("required_ingredients"):
        parts.append("with " + ", ".join(params["required_ingredients"]))
    if params.get("excluded_ingredients"):
        parts.append("without " + ", ".join(params["excluded_ingredients"]))
    return " · ".join(parts)


def record_search(repo, user_id: int, kind: str, text: str, params: dict, result_count: int) -> None:
    """Add a search to the user's history (repeating the latest search just refreshes it), then commit."""
    conn = repo.connection
    latest = query_one(
        repo,
        "SELECT search_id, kind, params FROM search_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    if latest and latest["kind"] == kind and latest["params"] == params:
        conn.execute(
            "UPDATE search_history SET created_at = now(), result_count = %s WHERE search_id = %s",
            (result_count, latest["search_id"]),
        )
    else:
        conn.execute(
            """INSERT INTO search_history (user_id, kind, query, params, result_count)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, kind, text[:300], Jsonb(params), result_count),
        )
        conn.execute(
            """DELETE FROM search_history WHERE user_id = %s AND search_id NOT IN (
                   SELECT search_id FROM search_history WHERE user_id = %s
                   ORDER BY created_at DESC LIMIT %s)""",
            (user_id, user_id, HISTORY_KEEP),
        )
    conn.commit()


# ---------- sign up / sign in ----------

@router.post("/auth/register", response_model=AuthResponse, status_code=201, tags=["account"])
def register(body: RegisterBody, repo=Depends(get_repo)):
    """Create an account and sign in."""
    if query_one(repo, "SELECT 1 FROM users WHERE lower(email) = %s", (body.email,)):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = query_one(
        repo,
        """INSERT INTO users (email, display_name, password_hash) VALUES (%s, %s, %s)
           RETURNING user_id, email, display_name, created_at""",
        (body.email, body.display_name, hash_password(body.password)),
    )
    repo.connection.execute("INSERT INTO user_profiles (user_id) VALUES (%s)", (user["user_id"],))
    token = create_session(repo, user["user_id"])
    repo.connection.commit()
    return AuthResponse(token=token, user=me(repo, user))


@router.post("/auth/login", response_model=AuthResponse, tags=["account"])
def login(body: LoginBody, repo=Depends(get_repo)):
    """Sign in with email and password."""
    if not login_allowed(body.email.strip().lower()):
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Try again later.")
    row = query_one(
        repo,
        "SELECT user_id, email, display_name, created_at, password_hash FROM users WHERE lower(email) = %s",
        (body.email,),
    )
    # Always run one hash check, so an unknown email is not faster to answer than a wrong password.
    ok = verify_password(body.password, row["password_hash"] if row else _DUMMY_HASH)
    if not row or not ok:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    row.pop("password_hash")
    token = create_session(repo, row["user_id"])
    repo.connection.commit()
    return AuthResponse(token=token, user=me(repo, row))


@router.post("/auth/logout", status_code=204, tags=["account"])
def logout(token: str | None = Depends(bearer_token), repo=Depends(get_repo)):
    """Sign out this browser (ends the session). Works even if already signed out."""
    if token:
        delete_session(repo, token)
        repo.connection.commit()
    return Response(status_code=204)


# ---------- profile ----------

@router.get("/me", response_model=Me, tags=["account"])
def get_me(user=Depends(current_user), repo=Depends(get_repo)):
    """The signed-in user and their profile."""
    return me(repo, user)


@router.put("/me/profile", response_model=Me, tags=["account"])
def update_profile(body: Profile, user=Depends(current_user), repo=Depends(get_repo)):
    """Replace the profile (send every field; missing ones are cleared)."""
    repo.connection.execute(
        f"""INSERT INTO user_profiles (user_id, {PROFILE_COLUMNS}, updated_at)
            VALUES (%(user_id)s, %(skin_type)s, %(goals)s, %(avoided_ingredients)s, %(fragrance_free)s,
                    %(max_price)s, %(preferred_category)s, now())
            ON CONFLICT (user_id) DO UPDATE SET
                skin_type = EXCLUDED.skin_type, goals = EXCLUDED.goals,
                avoided_ingredients = EXCLUDED.avoided_ingredients, fragrance_free = EXCLUDED.fragrance_free,
                max_price = EXCLUDED.max_price, preferred_category = EXCLUDED.preferred_category,
                updated_at = now()""",
        {**body.model_dump(), "user_id": user["user_id"]},
    )
    repo.connection.commit()
    return me(repo, user)


# ---------- search history ----------

@router.get("/me/history", response_model=list[HistoryItem], tags=["account"])
def history(limit: int = Query(50, ge=1, le=HISTORY_KEEP), user=Depends(current_user), repo=Depends(get_repo)):
    """The user's searches, newest first."""
    return query(
        repo,
        """SELECT search_id, kind, query, params, result_count, created_at FROM search_history
           WHERE user_id = %s ORDER BY created_at DESC LIMIT %s""",
        (user["user_id"], limit),
    )


@router.delete("/me/history", status_code=204, tags=["account"])
def clear_history(user=Depends(current_user), repo=Depends(get_repo)):
    """Delete the whole search history."""
    repo.connection.execute("DELETE FROM search_history WHERE user_id = %s", (user["user_id"],))
    repo.connection.commit()
    return Response(status_code=204)


@router.delete("/me/history/{search_id}", status_code=204, tags=["account"])
def delete_history_item(search_id: int, user=Depends(current_user), repo=Depends(get_repo)):
    """Delete one search from the history."""
    cur = repo.connection.execute(
        "DELETE FROM search_history WHERE search_id = %s AND user_id = %s", (search_id, user["user_id"])
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="No such search in your history.")
    repo.connection.commit()
    return Response(status_code=204)


# ---------- saved products ----------

@router.get("/me/saved", response_model=list[SavedProduct], tags=["account"])
def saved(user=Depends(current_user), repo=Depends(get_repo)):
    """Saved products, most recently saved first."""
    return query(
        repo,
        """SELECT p.product_id, p.product_name, p.brand, p.category, p.subcategory, p.price, p.rating,
                  p.review_count, s.created_at AS saved_at
           FROM saved_products s JOIN products p USING (product_id)
           WHERE s.user_id = %s ORDER BY s.created_at DESC""",
        (user["user_id"],),
    )


@router.put("/me/saved/{product_id}", status_code=204, tags=["account"])
def save_product(product_id: str, user=Depends(current_user), repo=Depends(get_repo)):
    """Save a product (saving it twice is fine)."""
    if not query_one(repo, "SELECT 1 FROM products WHERE product_id = %s", (product_id,)):
        raise HTTPException(status_code=404, detail=f"No product with id {product_id}")
    repo.connection.execute(
        "INSERT INTO saved_products (user_id, product_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (user["user_id"], product_id),
    )
    repo.connection.commit()
    return Response(status_code=204)


@router.delete("/me/saved/{product_id}", status_code=204, tags=["account"])
def unsave_product(product_id: str, user=Depends(current_user), repo=Depends(get_repo)):
    """Remove a saved product (removing one that is not saved is fine)."""
    repo.connection.execute(
        "DELETE FROM saved_products WHERE user_id = %s AND product_id = %s", (user["user_id"], product_id)
    )
    repo.connection.commit()
    return Response(status_code=204)
