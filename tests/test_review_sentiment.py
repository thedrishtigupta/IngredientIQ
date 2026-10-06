from src.reviews.sentiment import (
    add_review,
    aspects_in,
    build_signal,
    new_totals,
    pick_text,
    sentiment,
    smoothed_score,
    split_sentences,
)


def test_sentiment_sign():
    assert sentiment("I love this cream, it is amazing!") > 0.05
    assert sentiment("Terrible product, I hate it.") < -0.05


def test_pick_text_falls_back_to_title():
    assert pick_text("Great", "Really nice cream") == "Really nice cream"
    assert pick_text("Great", "") == "Great"
    assert pick_text("Great", None) == "Great"
    assert pick_text(None, "   ") is None


def test_smoothing_few_reviews_close_to_global():
    # 1 very happy review barely moves the score away from the global mean.
    score = smoothed_score(1.0, 1, 0.8)
    assert abs(score - 0.8) < 0.02


def test_smoothing_many_reviews_close_to_own_score():
    # 2000 reviews with average sentiment 0.2 -> own score 0.6.
    score = smoothed_score(0.2, 2000, 0.8)
    assert abs(score - 0.6) < 0.01


def test_split_sentences():
    assert split_sentences("Smells great. Feels sticky!\nWould buy again") == [
        "Smells great.",
        "Feels sticky!",
        "Would buy again",
    ]


def test_aspect_matching():
    assert aspects_in("It is so hydrating") == ["hydration"]
    assert aspects_in("The smell is lovely but the pump broke") == ["scent", "packaging"]
    assert aspects_in("It broke me out") == ["irritation"]
    assert aspects_in("I do the laundry") == []  # "dry" must not match inside "laundry"


def test_add_review_and_build_signal():
    totals = new_totals()
    add_review(totals, "Love it", "Smells amazing. Great price!")
    add_review(totals, "Bad", "Awful, it burns my skin.")
    add_review(totals, None, None)  # nothing to score, but still counts as a review

    assert totals["review_count"] == 3
    assert totals["analyzed_count"] == 2
    assert totals["positive"] == 1
    assert totals["negative"] == 1

    signal = build_signal(totals, global_score=0.8)
    assert signal["review_count"] == 3
    assert signal["analyzed_count"] == 2
    assert signal["positive_share"] == 0.5
    assert 0 <= signal["review_score"] <= 1
    assert signal["aspects"] == {}  # each aspect has fewer than 5 mentions


def test_aspects_need_enough_mentions():
    totals = new_totals()
    for _ in range(5):
        add_review(totals, None, "I love the scent.")
    add_review(totals, None, "The pump is bad.")

    aspects = build_signal(totals, global_score=0.8)["aspects"]
    assert aspects == {"scent": {"mentions": 5, "positive_share": 1.0}}


def test_product_without_scored_reviews_has_no_numbers():
    totals = new_totals()
    add_review(totals, None, "")
    signal = build_signal(totals, global_score=0.8)
    assert signal["review_count"] == 1
    assert signal["review_score"] is None
