"""Accounts: sign up / in / out, profile, search history, saved products, "for you".
Password hashing is tested without a database; the rest needs Postgres and skips without it.
Every test user is deleted afterwards (ON DELETE CASCADE removes sessions, history, saved items)."""
import uuid

import pytest
from fastapi.testclient import TestClient

from src.api.auth import hash_password, verify_password
from src.api.main import app
from src.recommender.repository import ProductRepository
from tests.test_api import needs_db

PASSWORD = "correct horse battery"


# ---------- no database needed ----------

def test_password_hash_round_trip():
    stored = hash_password(PASSWORD)
    assert stored.startswith("scrypt$") and PASSWORD not in stored
    assert verify_password(PASSWORD, stored)
    assert not verify_password("wrong password", stored)
    assert hash_password(PASSWORD) != stored  # random salt each time


@pytest.mark.parametrize("stored", ["", "plain", "bcrypt$1$2$3$aa$bb", "scrypt$x$8$1$zz$yy"])
def test_verify_rejects_malformed_hashes(stored):
    assert verify_password(PASSWORD, stored) is False


# ---------- need the database ----------

@pytest.fixture(scope="module")
def client():
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("OPENROUTER_API_KEY", "")
        with TestClient(app) as c:
            yield c


@needs_db
def test_cannot_touch_another_users_history(client, account):
    headers, _ = account
    client.get("/products", params={"q": "serum", "record_history": True}, headers=headers)
    search_id = client.get("/me/history", headers=headers).json()[0]["search_id"]
    other = client.post(
        "/auth/register",
        json={"email": f"test-{uuid.uuid4().hex[:12]}@example.com", "password": PASSWORD, "display_name": "Other"},
    ).json()
    try:
        other_headers = {"Authorization": f"Bearer {other['token']}"}
        assert client.get("/me/history", headers=other_headers).json() == []
        assert client.delete(f"/me/history/{search_id}", headers=other_headers).status_code == 404
        assert len(client.get("/me/history", headers=headers).json()) == 1
    finally:
        repo = ProductRepository()
        repo.connection.execute("DELETE FROM users WHERE user_id = %s", (other["user"]["user_id"],))
        repo.connection.commit()
        repo.close()


@pytest.fixture
def account(client):
    """A fresh signed-in user: (auth headers, user json). Deleted afterwards."""
    email = f"test-{uuid.uuid4().hex[:12]}@example.com"
    r = client.post("/auth/register", json={"email": email, "password": PASSWORD, "display_name": "Test"})
    assert r.status_code == 201, r.text
    body = r.json()
    yield {"Authorization": f"Bearer {body['token']}"}, body["user"]
    repo = ProductRepository()
    try:
        repo.connection.execute("DELETE FROM users WHERE user_id = %s", (body["user"]["user_id"],))
        repo.connection.commit()
    finally:
        repo.close()


@needs_db
def test_register_login_logout(client, account):
    headers, user = account
    assert user["email"].endswith("@example.com") and user["profile"]["goals"] == []
    assert client.get("/me", headers=headers).json()["user_id"] == user["user_id"]

    # Same email again (any case) is refused.
    dup = client.post("/auth/register", json={"email": user["email"].upper(), "password": PASSWORD, "display_name": "X"})
    assert dup.status_code == 409

    # Login works with any case and spaces; wrong password and unknown email give the same answer.
    ok = client.post("/auth/login", json={"email": f"  {user['email'].upper()} ", "password": PASSWORD})
    assert ok.status_code == 200
    second = {"Authorization": f"Bearer {ok.json()['token']}"}
    bad = client.post("/auth/login", json={"email": user["email"], "password": "nope-nope"})
    unknown = client.post("/auth/login", json={"email": "nobody-xyz@example.com", "password": PASSWORD})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json()["detail"] == unknown.json()["detail"]

    # Logging out ends only that session.
    assert client.post("/auth/logout", headers=second).status_code == 204
    assert client.get("/me", headers=second).status_code == 401
    assert client.get("/me", headers=headers).status_code == 200


@needs_db
@pytest.mark.parametrize(
    "body",
    [
        {"email": "not-an-email", "password": PASSWORD, "display_name": "A"},
        {"email": "a@example.com", "password": "short", "display_name": "A"},
        {"email": "a@example.com", "password": PASSWORD, "display_name": "   "},
    ],
)
def test_register_validation(client, body):
    assert client.post("/auth/register", json=body).status_code == 422


@needs_db
def test_me_endpoints_need_a_valid_token(client):
    assert client.get("/me").status_code == 401
    assert client.get("/me/history", headers={"Authorization": "Bearer made-up"}).status_code == 401
    assert client.get("/me/saved", headers={"Authorization": "Basic abc"}).status_code == 401


@needs_db
def test_profile_update_and_validation(client, account):
    headers, _ = account
    profile = {
        "skin_type": "Sensitive",
        "goals": ["soothing", "barrier_support"],
        "avoided_ingredients": ["Alcohol", " alcohol ", "Fragrance"],
        "fragrance_free": True,
        "max_price": 40,
        "preferred_category": "Skincare",
    }
    saved = client.put("/me/profile", json=profile, headers=headers).json()["profile"]
    assert saved["skin_type"] == "sensitive"
    assert saved["avoided_ingredients"] == ["alcohol", "fragrance"]
    assert client.get("/me", headers=headers).json()["profile"] == saved

    assert client.put("/me/profile", json={"goals": ["flying"]}, headers=headers).status_code == 422
    assert client.put("/me/profile", json={"skin_type": "scaly"}, headers=headers).status_code == 422


@needs_db
def test_search_history_is_recorded_only_when_asked(client, account):
    headers, _ = account
    # Not signed in, or no flag, or empty text: nothing is recorded.
    client.get("/products", params={"q": "serum", "record_history": True})
    client.get("/products", params={"q": "serum"}, headers=headers)
    client.get("/products", params={"q": "  ", "record_history": True}, headers=headers)
    client.post("/recommend", json={"goals": ["hydration"], "top_k": 3}, headers=headers)
    assert client.get("/me/history", headers=headers).json() == []

    client.get("/products", params={"q": "drunk elephant", "record_history": True}, headers=headers)
    client.get("/products", params={"q": "drunk elephant", "record_history": True}, headers=headers)  # repeat
    rec = {"goals": ["hydration"], "category": "Skincare", "max_price": 50,
           "excluded_ingredients": ["fragrance"], "top_k": 3, "explain": False, "record_history": True}
    assert client.post("/recommend", json=rec, headers=headers).status_code == 200

    history = client.get("/me/history", headers=headers).json()
    assert [h["kind"] for h in history] == ["recommend", "text"]  # newest first, repeat merged
    assert history[1]["query"] == "drunk elephant" and history[1]["result_count"] > 0
    assert history[0]["query"] == "Hydration · Skincare · under $50 · without fragrance"
    assert history[0]["params"]["goals"] == ["hydration"] and "record_history" not in history[0]["params"]

    # Delete one, then clear all. An id that is not (or no longer) in your history is a 404.
    assert client.delete(f"/me/history/{history[1]['search_id']}", headers=headers).status_code == 204
    assert client.delete(f"/me/history/{history[1]['search_id']}", headers=headers).status_code == 404
    assert len(client.get("/me/history", headers=headers).json()) == 1
    assert client.delete("/me/history", headers=headers).status_code == 204
    assert client.get("/me/history", headers=headers).json() == []


@needs_db
def test_saved_products(client, account):
    headers, _ = account
    ids = [p["product_id"] for p in client.get("/products", params={"q": "serum", "limit": 2}).json()]
    for pid in ids:
        assert client.put(f"/me/saved/{pid}", headers=headers).status_code == 204
    assert client.put(f"/me/saved/{ids[0]}", headers=headers).status_code == 204  # twice is fine
    assert client.put("/me/saved/NOPE", headers=headers).status_code == 404

    saved = client.get("/me/saved", headers=headers).json()
    assert [p["product_id"] for p in saved] == ids[::-1]  # most recent first
    assert client.delete(f"/me/saved/{ids[0]}", headers=headers).status_code == 204
    assert [p["product_id"] for p in client.get("/me/saved", headers=headers).json()] == [ids[1]]


@needs_db
def test_recommendations_follow_the_profile(client, account):
    headers, _ = account
    client.put(
        "/me/profile",
        json={"goals": ["hydration"], "fragrance_free": True, "max_price": 30, "preferred_category": "Skincare"},
        headers=headers,
    )
    data = client.get("/me/recommendations", params={"top_k": 5}, headers=headers).json()
    assert data["request"]["goals"] == ["hydration"]
    assert data["request"]["excluded_ingredients"] == ["fragrance"]
    assert 0 < data["count"] <= 5
    assert all(r["category"] == "Skincare" and r["price"] <= 30 for r in data["results"])
