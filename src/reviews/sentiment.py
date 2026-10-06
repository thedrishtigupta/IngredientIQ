"""Review sentiment: turn raw review text into a few numbers per product.

The idea, step by step:
1. VADER (a rule-based sentiment scorer, no training, no download) gives every
   review a "compound" score from -1 (very negative) to +1 (very positive).
2. We also split each review into sentences. A sentence that mentions an
   aspect (hydration, scent, packaging, ...) is scored on its own, so we can
   say "people who talk about scent are 80% positive".
3. Per product we add everything up, then turn the average sentiment into one
   review_score between 0 and 1 (see smoothed_score below).

Upgrade path: a transformer sentiment model could replace sentiment() later.
"""

import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

METHOD = "vader_v1"
POSITIVE_ABOVE = 0.05       # compound above this counts as positive
NEGATIVE_BELOW = -0.05      # compound below this counts as negative
SMOOTHING_M = 20            # "pretend every product has 20 average reviews"
MIN_ASPECT_MENTIONS = 5     # ignore aspects mentioned fewer times than this

# Each keyword matches the START of a word ("hydrat" -> hydrating, hydration).
ASPECT_WORDS = {
    "hydration": ["hydrat", "moistur", "dry", "dewy"],
    "texture": ["textur", "creamy", "greasy", "sticky", "thick", "lightweight", "silky"],
    "scent": ["scent", "smell", "fragranc", "perfum"],
    "irritation": ["irritat", "sensitiv", "breakout", "break out", "broke me out",
                   "burn", "sting", "redness", "rash", "itch"],
    "absorption": ["absorb", "sinks", "soaks", "residue"],
    "packaging": ["packag", "bottle", "pump", "jar", "tube", "lid"],
    "value": ["price", "pricey", "expensive", "cheap", "worth", "value", "money"],
    "effectiveness": ["result", "effective", "works", "worked", "difference", "improve"],
}
ASPECT_PATTERNS = {
    name: re.compile(r"\b(?:" + "|".join(words) + ")")
    for name, words in ASPECT_WORDS.items()
}

analyzer = SentimentIntensityAnalyzer()


def sentiment(text):
    """VADER compound score of a piece of text, -1 .. 1."""
    return analyzer.polarity_scores(text)["compound"]


def pick_text(title, text):
    """Use the review text; fall back to the title; None if both are empty."""
    for candidate in (text, title):
        if candidate and candidate.strip():
            return candidate.strip()
    return None


def split_sentences(text):
    """Cut text after . ! ? or at line breaks."""
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part for part in parts if part.strip()]


def aspects_in(sentence):
    """Names of the aspects whose keywords appear in this sentence."""
    lower = sentence.lower()
    return [name for name, pattern in ASPECT_PATTERNS.items() if pattern.search(lower)]


def new_totals():
    """Empty running totals for one product."""
    return {
        "review_count": 0,
        "analyzed_count": 0,
        "sentiment_sum": 0.0,
        "positive": 0,
        "negative": 0,
        "aspects": {},  # name -> [mentions, positive_mentions]
    }


def add_review(totals, title, text):
    """Score one review and add it to the product's running totals."""
    totals["review_count"] += 1
    body = pick_text(title, text)
    if body is None:
        return  # nothing to score

    compound = sentiment(body)
    totals["analyzed_count"] += 1
    totals["sentiment_sum"] += compound
    if compound > POSITIVE_ABOVE:
        totals["positive"] += 1
    elif compound < NEGATIVE_BELOW:
        totals["negative"] += 1

    for sentence in split_sentences(body):
        names = aspects_in(sentence)
        if not names:
            continue
        sentence_score = sentiment(sentence)
        for name in names:
            counts = totals["aspects"].setdefault(name, [0, 0])
            counts[0] += 1
            if sentence_score > POSITIVE_ABOVE:
                counts[1] += 1


def smoothed_score(avg_sentiment, n, global_score, m=SMOOTHING_M):
    """Review score in 0..1, pulled toward the global average.

    Step 1: move the average sentiment from -1..1 onto 0..1.
    Step 2: a product with only 2 reviews could be lucky or unlucky, so we mix
    in m "pretend average reviews". With n real reviews the result is
        (n * own_score + m * global_score) / (n + m)
    Few reviews -> close to the global average. Many reviews -> close to own score.
    """
    own_score = (avg_sentiment + 1) / 2
    return (n * own_score + m * global_score) / (n + m)


def build_signal(totals, global_score):
    """Turn one product's running totals into the values stored in the table."""
    n = totals["analyzed_count"]
    aspects = {
        name: {"mentions": mentions, "positive_share": round(positive / mentions, 3)}
        for name, (mentions, positive) in totals["aspects"].items()
        if mentions >= MIN_ASPECT_MENTIONS
    }
    signal = {
        "review_count": totals["review_count"],
        "analyzed_count": n,
        "avg_sentiment": None,
        "positive_share": None,
        "negative_share": None,
        "review_score": None,
        "aspects": aspects,
    }
    if n > 0:  # no scored reviews -> no invented numbers
        avg = totals["sentiment_sum"] / n
        signal["avg_sentiment"] = round(avg, 4)
        signal["positive_share"] = round(totals["positive"] / n, 4)
        signal["negative_share"] = round(totals["negative"] / n, 4)
        signal["review_score"] = round(smoothed_score(avg, n, global_score), 4)
    return signal
