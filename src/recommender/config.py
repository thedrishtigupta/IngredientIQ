# Hybrid recommender (ingredient match + vector similarity + review signal).
# Sum = 1.0. A product with no review signal drops "review" and the rest are
# renormalised, so un-reviewed products are not punished or given invented data.
# With no goals in the request, goal / similarity / intent are dropped the same way.
HYBRID_WEIGHTS = {
    "goal": 0.30,        # share of the goal's ingredients present (ingredient match)
    "similarity": 0.20,  # cosine similarity between goal vector and product vector
    "intent": 0.15,      # product type fits the goal
    "review": 0.15,      # review sentiment score from review NLP
    "rating": 0.12,
    "popularity": 0.08,
}

# Goals we show to users (goal id -> label). The database knows more goal ids
# (stability, texture, skin_feel ...) but those describe the formula, not a user wish.
GOAL_LABELS = {
    "hydration": "Hydration",
    "moisturization": "Moisturization",
    "brightening": "Brightening",
    "exfoliation": "Exfoliation",
    "antioxidant": "Antioxidant protection",
    "soothing": "Soothing",
    "oil_control": "Oil control",
    "uv_protection": "UV protection",
    "cleansing": "Cleansing",
    "barrier_support": "Skin barrier support",
    "hair_conditioning": "Hair conditioning",
}

# A product with no reviews is scored as if its review score were this typical
# value (the average review_score of reviewed products), so having reviews is not
# a bonus and not having them is not a penalty. Only Skincare has review data.
# The result still shows review_score = None ("no review data") - nothing is faked.
NEUTRAL_REVIEW_SCORE = 0.84

# Product type score when the goal has a type list but this type is not on it
# (e.g. eyeshadow for oil control): clearly worse than any listed type.
UNLISTED_SUBCATEGORY_INTENT = 0.25

# Review aspects with fewer mentions than this are too thin to quote in an explanation.
MIN_ASPECT_MENTIONS = 10

# Aspects whose "positive share" cannot be trusted. Irritation sentences are
# negative-sounding even in happy reviews ("no irritation at all"), so a low
# share does not mean the product irritates people. We keep the data but never
# quote it in an explanation.
UNRELIABLE_ASPECTS = {"irritation"}


GOAL_SUBCATEGORY_AFFINITY = {
    "hydration": {
        "Moisturizers": 1.00,
        "Body Moisturizers": 0.95,
        "Treatments": 0.85,
        "Masks": 0.80,
        "Eye Care": 0.70,
        "Lip Balms & Treatments": 0.60,
        "Cleansers": 0.45,
        "Value & Gift Sets": 0.35,
        "Mini Size": 0.35,
        "Sunscreen": 0.30,
        "High Tech Tools": 0.10,
    },

    "brightening": {
        "Treatments": 1.00,
        "Moisturizers": 0.90,
        "Masks": 0.85,
        "Eye Care": 0.80,
        "Cleansers": 0.60,
        "Value & Gift Sets": 0.35,
        "Mini Size": 0.35,
    },

    "exfoliation": {
        "Treatments": 1.00,
        "Cleansers": 0.90,
        "Masks": 0.90,
        "Moisturizers": 0.55,
        "Eye Care": 0.40,
        "Value & Gift Sets": 0.30,
        "Mini Size": 0.30,
    },

    "hair_conditioning": {
        "Shampoo & Conditioner": 1.00,
        "Hair Styling & Treatments": 0.90,
        "Masks": 0.85,
        "Value & Gift Sets": 0.35,
        "Mini Size": 0.35,
    },

    # Goals below were added with the hybrid engine. A subcategory that is not
    # listed gets the neutral 0.5.
    "moisturization": {
        "Moisturizers": 1.00,
        "Body Moisturizers": 0.95,
        "Masks": 0.80,
        "Treatments": 0.75,
        "Eye Care": 0.70,
        "Lip Balms & Treatments": 0.65,
        "Cleansers": 0.40,
        "Sunscreen": 0.30,
        "Value & Gift Sets": 0.35,
        "Mini Size": 0.35,
    },

    "antioxidant": {
        "Treatments": 1.00,
        "Moisturizers": 0.85,
        "Eye Care": 0.80,
        "Masks": 0.70,
        "Sunscreen": 0.60,
        "Cleansers": 0.40,
        "Value & Gift Sets": 0.35,
        "Mini Size": 0.35,
    },

    "soothing": {
        "Treatments": 0.90,
        "Moisturizers": 0.90,
        "Masks": 0.85,
        "Body Moisturizers": 0.80,
        "Eye Care": 0.75,
        "Lip Balms & Treatments": 0.60,
        "Cleansers": 0.50,
        "Sunscreen": 0.40,
        "Value & Gift Sets": 0.35,
        "Mini Size": 0.35,
    },

    "oil_control": {
        "Treatments": 0.90,
        "Cleansers": 0.90,
        "Masks": 0.85,
        "Moisturizers": 0.70,
        "Sunscreen": 0.50,
        "Eye Care": 0.20,
        "Value & Gift Sets": 0.30,
        "Mini Size": 0.30,
    },

    "uv_protection": {
        "Sunscreen": 1.00,
        "Moisturizers": 0.70,
        "Body Moisturizers": 0.50,
        "Lip Balms & Treatments": 0.50,
        "Treatments": 0.40,
        "Eye Care": 0.40,
        "Cleansers": 0.10,
        "Value & Gift Sets": 0.30,
        "Mini Size": 0.30,
    },

    "cleansing": {
        "Cleansers": 1.00,
        "Bath & Shower": 0.90,
        "Shampoo & Conditioner": 0.80,
        "Masks": 0.60,
        "Treatments": 0.40,
        "Moisturizers": 0.20,
        "Value & Gift Sets": 0.30,
        "Mini Size": 0.30,
    },

    "barrier_support": {
        "Moisturizers": 1.00,
        "Treatments": 0.85,
        "Body Moisturizers": 0.85,
        "Eye Care": 0.70,
        "Lip Balms & Treatments": 0.70,
        "Masks": 0.70,
        "Cleansers": 0.40,
        "Sunscreen": 0.40,
        "Value & Gift Sets": 0.35,
        "Mini Size": 0.35,
    },
}