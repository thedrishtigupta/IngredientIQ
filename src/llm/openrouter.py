"""
Plain-English explanations for recommended products, written by an LLM.

How it works (the important part):
  - The database and the scoring code have ALREADY chosen and scored the
    products. This file never chooses anything.
  - We send the model only those computed facts (name, ingredients, scores...)
    and ask it to put them into 2-3 friendly sentences per product.
  - We make ONE request to OpenRouter for all products (cheaper and faster).
  - If anything goes wrong (no API key, timeout, HTTP error, unreadable reply)
    we use `template_summary` instead, a fixed sentence built from the same
    facts. So explain_results() never raises and always answers every product.
"""

import json
import logging
import os

import httpx
from dotenv import load_dotenv

from src.recommender.config import MIN_ASPECT_MENTIONS, UNRELIABLE_ASPECTS

load_dotenv()  # read OPENROUTER_API_KEY / OPENROUTER_MODEL from .env (once, at import)

URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash-lite"  # small and cheap; override with OPENROUTER_MODEL

log = logging.getLogger(__name__)

RULES = (
    "You write short product explanations for a beauty product recommender. "
    "The products were already chosen and scored by our database; you only describe them.\n"
    "Rules:\n"
    "- Use ONLY the facts given for each product. Never invent ingredients, numbers, "
    "benefits or products.\n"
    "- Make no medical or dermatological claims (never say a product treats, cures, "
    "heals or fixes a skin condition).\n"
    "- Mention an ingredient ONLY if it is in that product's matched_ingredients. Do not "
    "describe ingredients or benefits that appear only in the product name.\n"
    "- user_choices says what the shopper asked for (goals, category, budget, fragrance-free...). "
    "Every product already satisfies these choices, so you may say how it fits them, "
    "e.g. 'at $30 it is within your $50 budget'. For fragrance-free say 'no fragrance or "
    "parfum listed', never 'free of all fragrance allergens'.\n"
    "- Write 2 to 3 friendly plain-English sentences per product.\n"
    '- Reply with ONLY a JSON object mapping each product id to its text, like '
    '{"P123": "..."}. No markdown and no extra keys.'
)


def llm_enabled() -> bool:
    """True only if an OpenRouter key is set (and not just blank spaces)."""
    return bool(os.getenv("OPENROUTER_API_KEY", "").strip())


def _best_worst_aspect(aspects: dict):
    """From {"hydration": {"mentions": 120, "positive_share": 0.91}, ...} return
    ((name, share) best, (name, share) worst). Either is None if not available."""
    shares = {
        name: float(info["positive_share"])
        for name, info in (aspects or {}).items()
        if isinstance(info, dict) and info.get("positive_share") is not None
        and name not in UNRELIABLE_ASPECTS
        and info.get("mentions", 0) >= MIN_ASPECT_MENTIONS
    }
    if not shares:
        return None, None
    best = max(shares, key=shares.get)
    worst = min(shares, key=shares.get)
    return (best, shares[best]), ((worst, shares[worst]) if worst != best else None)


def user_choices(request) -> dict:
    """What the shopper asked for, as a small dict for the LLM (empty choices are left out).
    `request` is a RecommendationRequest (or anything with the same attributes)."""
    excluded = [x.strip().lower() for x in (request.excluded_ingredients or [])]
    choices = {
        "goals": list(request.goals or []),
        "category": request.category,
        "subcategory": request.subcategory,
        "min_price_usd": request.min_price,
        "max_price_usd": request.max_price,
        "fragrance_free": any(x in ("fragrance", "parfum") for x in excluded),
        "excluded_ingredients": [x for x in excluded if x not in ("fragrance", "parfum")],
        "required_ingredients": list(request.required_ingredients or []),
    }
    return {k: v for k, v in choices.items() if v not in (None, [], False)}


def _num(x):
    """Round a number to 2 decimals (None stays None, Decimal becomes float)."""
    return None if x is None else round(float(x), 2)


def _facts(r) -> dict:
    """The ONLY information about a product that is sent to the LLM."""
    best, worst = _best_worst_aspect(r.aspects)
    expl = r.explanation
    return {
        "id": r.product_id,
        "name": r.product_name,
        "brand": r.brand,
        "price": _num(r.price),
        "rating": _num(r.rating),
        "matched_ingredients": list(r.matched_ingredients)[:8],
        "matched_goals": list(r.matched_goals),
        "goal_match_score": _num(r.goal_match_score),
        "vector_similarity": _num(r.similarity_score),
        "review_sentiment_score": _num(r.review_score),
        "best_aspect": best and {"name": best[0], "positive_share": round(best[1], 2)},
        "worst_aspect": worst and {"name": worst[0], "positive_share": round(worst[1], 2)},
        "strengths": list(expl.strengths) if expl else [],
        "weaknesses": list(expl.weaknesses) if expl else [],
    }


def template_summary(result, goals: list[str]) -> str:
    """Fixed 2-sentence fallback. Uses only facts already on the result."""
    goal_text = " and ".join(result.matched_goals or goals) or "your goals"
    who = result.product_name + (f" by {result.brand}" if result.brand else "")
    ingredients = ", ".join(result.matched_ingredients[:3])
    if ingredients:
        first = f"{who} is a recommended option for {goal_text}, with ingredients such as {ingredients}."
    else:
        first = f"{who} is a recommended option for {goal_text}."

    parts = []
    if result.rating is not None:
        parts.append(f"a {float(result.rating):.1f}/5 rating")
    if result.review_score is not None:
        parts.append(f"a review sentiment score of {float(result.review_score):.2f}")
    best, _ = _best_worst_aspect(result.aspects)
    if best:
        parts.append(f"mostly positive review mentions of {best[0]}")
    if result.price is not None:
        parts.append(f"a price of ${float(result.price):.2f}")
    if len(parts) > 1:
        parts = [", ".join(parts[:-1]) + " and " + parts[-1]]
    second = f"It has {parts[0]}." if parts else "We have no rating or price data for it."
    return f"{first} {second}"


def _parse_reply(content) -> dict[str, str]:
    """Turn the model's text into {product_id: text}. Tolerates ```json fences
    and chatter around the JSON. Raises ValueError if there is no usable object."""
    if not isinstance(content, str):
        raise ValueError("reply is not text")
    start, end = content.find("{"), content.rfind("}")
    data = json.loads(content[start : end + 1])  # slicing drops fences and chatter
    if not isinstance(data, dict):
        raise ValueError("reply is not a JSON object")
    return {str(k): v.strip() for k, v in data.items() if isinstance(v, str) and v.strip()}


def _ask_llm(results, goals, timeout, client, choices=None) -> dict[str, str]:
    """One batched OpenRouter call. May raise; explain_results() catches it."""
    body = {
        "model": os.getenv("OPENROUTER_MODEL", "").strip() or DEFAULT_MODEL,
        "temperature": 0.2,
        # Cap the reply (~120 tokens per product). Without a cap OpenRouter reserves
        # the model's maximum (65k tokens) and refuses with HTTP 402 if the account's
        # credit balance cannot cover that.
        "max_tokens": 150 * max(len(results), 1) + 200,
        "messages": [
            {"role": "system", "content": RULES},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "requested_goals": goals,
                        "user_choices": choices or {"goals": goals},
                        "products": [_facts(r) for r in results],
                    }
                ),
            },
        ],
    }
    headers = {
        "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"].strip(),
        "X-Title": "IngredientIQ",
    }
    resp = (client or httpx).post(URL, json=body, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return _parse_reply(resp.json()["choices"][0]["message"]["content"])


def explain_results(results, goals: list[str], timeout: float = 30.0, client=None, choices=None) -> dict[str, str]:
    """Return {product_id: explanation} for EVERY result. Never raises.

    `client` is an optional httpx.Client (tests pass one with a fake transport).
    `choices` is the shopper's request as a dict (see user_choices); it lets the model say
    how a product fits the budget, category and so on.
    """
    fallback = {r.product_id: template_summary(r, goals) for r in results}
    if not results or not llm_enabled():
        return fallback
    try:
        texts = _ask_llm(results, goals, timeout, client, choices)
    except Exception as e:  # never crash the API because of the LLM
        log.warning("LLM explanation failed (%s); using templates", type(e).__name__)
        return fallback
    return {pid: texts.get(pid) or text for pid, text in fallback.items()}
