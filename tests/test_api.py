"""API tests. The ones marked DB need the Postgres container; they skip if it is not reachable.
The LLM is switched off (empty key), so no network call is ever made."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.recommender.repository import ProductRepository


def db_is_up():
    try:
        ProductRepository().close()
        return True
    except Exception:
        return False


needs_db = pytest.mark.skipif(not db_is_up(), reason="Postgres is not reachable")


@pytest.fixture(scope="module")
def client():
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("OPENROUTER_API_KEY", "")  # LLM off -> template explanations only
        with TestClient(app) as c:  # "with" runs the startup (builds the vector index)
            yield c


# ---------- no database needed ----------

def test_recommend_unknown_goal_is_422(client):
    r = client.post("/recommend", json={"goals": ["not_a_goal"]})
    assert r.status_code == 422
    assert "hydration" in r.text  # the message lists the valid goals


@pytest.mark.parametrize("top_k", [0, 21])
def test_recommend_top_k_out_of_range_is_422(client, top_k):
    assert client.post("/recommend", json={"goals": ["hydration"], "top_k": top_k}).status_code == 422


def test_goals(client):
    goals = client.get("/goals").json()
    assert "hydration" in [g["id"] for g in goals]
    assert all(set(g) == {"id", "label", "supported_by_vectors"} for g in goals)


def test_cors_allows_localhost_only(client):
    ok = client.get("/goals", headers={"Origin": "http://localhost:5173"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5173"
    other = client.get("/goals", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in other.headers


def test_search_limit_over_50_is_422(client):
    assert client.get("/products?limit=51").status_code == 422


# ---------- need the database ----------

@needs_db
def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["db"] is True
    assert body["llm_enabled"] is False
    assert body["products"] > 0
    assert 0 < body["reviewed_products"] <= body["products"] and body["reviews"] >= body["reviewed_products"]


@needs_db
def test_categories(client):
    cats = client.get("/categories").json()
    skincare = next(c for c in cats if c["category"] == "Skincare")
    assert skincare["product_count"] > 0 and skincare["subcategories"]


@needs_db
def test_recommend_hydration_skincare_under_50(client):
    r = client.post(
        "/recommend",
        json={"goals": ["hydration"], "category": "Skincare", "max_price": 50, "top_k": 5},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == len(body["results"]) > 0
    assert body["llm_used"] is False
    assert all(p["category"] == "Skincare" and p["price"] <= 50 for p in body["results"])
    scores = [p["score"] for p in body["results"]]
    assert scores == sorted(scores, reverse=True)
    assert all(p["explanation"]["summary"] for p in body["results"])  # template summaries
    assert abs(sum(body["weights"].values()) - 1) < 1e-9  # the frontend shows these next to each score part


@needs_db
def test_recommend_without_explain_has_no_summary(client):
    body = client.post("/recommend", json={"goals": ["hydration"], "top_k": 3, "explain": False}).json()
    assert all(p["explanation"]["summary"] is None for p in body["results"])


@needs_db
def test_product_detail_and_similar(client):
    pid = client.post("/recommend", json={"goals": ["hydration"], "top_k": 1}).json()["results"][0]["product_id"]

    detail = client.get(f"/products/{pid}").json()
    assert detail["product_id"] == pid
    assert detail["ingredients"] and {"name", "ingredient_id"} <= set(detail["ingredients"][0])
    assert {"functional_profile", "review_signals", "review_summary"} <= set(detail)

    similar = client.get(f"/products/{pid}/similar?k=3").json()
    assert 0 < len(similar) <= 3
    assert pid not in [p["product_id"] for p in similar]
    assert all(0 <= p["similarity"] <= 1 for p in similar)


@needs_db
def test_search(client):
    found = client.get("/products?q=cream&limit=5").json()
    assert 0 < len(found) <= 5
    assert all("cream" in (p["product_name"] + (p["brand"] or "")).lower() for p in found)


@needs_db
def test_unknown_product_is_404(client):
    assert client.get("/products/NOPE").status_code == 404
    assert client.get("/products/NOPE/similar").status_code == 404


def test_db_down_is_503(client, monkeypatch):
    monkeypatch.setenv("PGHOST", "127.0.0.1")  # skip the slow IPv4/IPv6 "localhost" lookup on Windows
    monkeypatch.setenv("PGPORT", "1")  # nothing listens on port 1
    monkeypatch.setenv("PGCONNECT_TIMEOUT", "1")  # fail fast
    r = client.get("/categories")
    assert r.status_code == 503
    assert "Database unreachable" in r.json()["detail"]
    assert client.get("/health").json()["db"] is False


@needs_db
def test_ingredient_list_and_detail(client):
    top = client.get("/ingredients?limit=5").json()
    assert len(top) == 5
    counts = [i["product_count"] for i in top]
    assert counts == sorted(counts, reverse=True) and counts[0] > 0

    found = client.get("/ingredients?q=hyaluronate&limit=3").json()
    assert found and all("hyaluronate" in i["name"] for i in found)

    detail = client.get(f"/ingredients/{top[0]['ingredient_id']}").json()
    assert detail["name"] == top[0]["name"] and detail["product_count"] == top[0]["product_count"]
    assert 0 < detail["catalog_share"] <= 1
    assert 0 < len(detail["related"]) <= 6 and detail["related"][0]["ingredient_id"] != detail["ingredient_id"]
    assert 0 < len(detail["products"]) <= 12


@needs_db
def test_unknown_ingredient_is_404(client):
    assert client.get("/ingredients/99999999").status_code == 404


def test_ingredient_limit_over_200_is_422(client):
    assert client.get("/ingredients?limit=201").status_code == 422
