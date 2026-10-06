import json
import logging

import httpx

from src.llm import openrouter
from src.llm.openrouter import explain_results, llm_enabled, template_summary
from src.recommender.models import RecommendationExplanation, RecommendationResult

KEY = "sk-or-test-secret-123"


def make_result(pid="P1", **overrides):
    data = dict(
        product_id=pid, product_name=f"Product {pid}", brand="Brand",
        category="Skincare", subcategory="Moisturizers",
        price=30.0, rating=4.7, review_count=1000, loves_count=500,
        score=0.8, goal_match_score=0.9, intent_score=0.9,
        rating_score=0.9, popularity_score=0.5,
        matched_goals=["hydration"],
        matched_ingredients=["glycerin", "hyaluronic acid", "squalane", "urea", "ceramide"],
        similarity_score=0.66, review_score=0.82,
        aspects={"hydration": {"mentions": 120, "positive_share": 0.91},
                 "scent": {"mentions": 40, "positive_share": 0.40}},
        explanation=RecommendationExplanation(strengths=["Highly rated at 4.70/5."], weaknesses=[]),
    )
    data.update(overrides)
    return RecommendationResult(**data)


def reply(content):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def fake_client(handler):
    """An httpx client that never touches the network; `handler` plays OpenRouter."""
    return httpx.Client(transport=httpx.MockTransport(handler))


def no_network(request):
    raise AssertionError("the network must not be called")


def test_llm_enabled_only_with_non_blank_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert llm_enabled() is False
    monkeypatch.setenv("OPENROUTER_API_KEY", "   ")
    assert llm_enabled() is False
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    assert llm_enabled() is True


def test_no_key_returns_templates_without_calling_network(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    results = [make_result("P1"), make_result("P2")]
    out = explain_results(results, ["hydration"], client=fake_client(no_network))
    assert out == {r.product_id: template_summary(r, ["hydration"]) for r in results}


def test_template_uses_only_known_facts():
    text = template_summary(make_result(), ["hydration"])
    assert "Product P1 by Brand" in text and "hydration" in text
    assert "glycerin, hyaluronic acid, squalane" in text
    assert "urea" not in text  # only the first few ingredients
    assert "4.7/5" in text and "0.82" in text and "$30.00" in text
    assert "mentions of hydration" in text  # best aspect
    assert text.count(".") >= 2


def test_template_survives_missing_data():
    bare = make_result(brand=None, price=None, rating=None, review_score=None,
                       aspects={}, matched_ingredients=[], matched_goals=[], explanation=None)
    text = template_summary(bare, [])
    assert "your goals" in text and "$" not in text and "None" not in text


def test_good_json_reply(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    results = [make_result("P1"), make_result("P2")]
    handler = lambda request: reply(json.dumps({"P1": "Nice one.", "P2": "Also nice."}))
    out = explain_results(results, ["hydration"], client=fake_client(handler))
    assert out == {"P1": "Nice one.", "P2": "Also nice."}


def test_fenced_json_reply(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    content = 'Sure! Here you go:\n```json\n{"P1": "Fenced text."}\n```'
    out = explain_results([make_result("P1")], ["hydration"], client=fake_client(lambda r: reply(content)))
    assert out == {"P1": "Fenced text."}


def test_partial_reply_falls_back_per_product(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    results = [make_result("P1"), make_result("P2")]
    handler = lambda request: reply(json.dumps({"P1": "Only this one.", "P9": "Unknown id."}))
    out = explain_results(results, ["hydration"], client=fake_client(handler))
    assert out["P1"] == "Only this one."
    assert out["P2"] == template_summary(results[1], ["hydration"])
    assert set(out) == {"P1", "P2"}  # ids the model made up are ignored


def test_http_error_timeout_and_garbage_fall_back_to_templates(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    results = [make_result("P1"), make_result("P2")]
    expected = {r.product_id: template_summary(r, ["hydration"]) for r in results}

    def timeout(request):
        raise httpx.ReadTimeout("too slow", request=request)

    handlers = [
        lambda r: httpx.Response(500, text="boom"),
        lambda r: httpx.Response(401, json={"error": "bad key"}),
        timeout,
        lambda r: reply("I am sorry, I cannot do that."),
        lambda r: reply('["not", "an", "object"]'),
        lambda r: reply(None),
        lambda r: httpx.Response(200, text="<html>not json</html>"),
    ]
    for handler in handlers:
        assert explain_results(results, ["hydration"], client=fake_client(handler)) == expected


def test_request_sends_model_key_and_only_allowed_facts(monkeypatch, caplog, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    monkeypatch.setenv("OPENROUTER_MODEL", "some/test-model")
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        seen["title"] = request.headers["X-Title"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(500)  # also exercises the failure log path

    with caplog.at_level(logging.DEBUG):
        explain_results([make_result("P1")], ["hydration"], client=fake_client(handler))

    assert seen["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert seen["auth"] == f"Bearer {KEY}" and seen["title"] == "IngredientIQ"
    body = seen["body"]
    assert body["model"] == "some/test-model" and body["temperature"] == 0.2
    assert KEY not in json.dumps(body)

    user = json.loads(body["messages"][1]["content"])
    assert user["requested_goals"] == ["hydration"]
    (product,) = user["products"]
    assert set(product) == {
        "id", "name", "brand", "price", "rating", "matched_ingredients", "matched_goals",
        "goal_match_score", "vector_similarity", "review_sentiment_score",
        "best_aspect", "worst_aspect", "strengths", "weaknesses",
    }
    assert product["matched_ingredients"] == ["glycerin", "hyaluronic acid", "squalane", "urea", "ceramide"]
    assert product["best_aspect"] == {"name": "hydration", "positive_share": 0.91}
    assert product["worst_aspect"] == {"name": "scent", "positive_share": 0.4}
    assert product["strengths"] == ["Highly rated at 4.70/5."]
    # nothing the scorer did not give us (e.g. loves_count, category) is sent
    assert "500" not in json.dumps(user) and "Skincare" not in json.dumps(user)

    # the key is never logged or printed
    assert KEY not in caplog.text
    captured = capsys.readouterr()
    assert KEY not in captured.out + captured.err


def test_default_model_when_env_unset(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    seen = {}

    def handler(request):
        seen["model"] = json.loads(request.content)["model"]
        return reply("{}")

    explain_results([make_result()], ["hydration"], client=fake_client(handler))
    assert seen["model"] == openrouter.DEFAULT_MODEL


def test_empty_results(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", KEY)
    assert explain_results([], ["hydration"], client=fake_client(no_network)) == {}
