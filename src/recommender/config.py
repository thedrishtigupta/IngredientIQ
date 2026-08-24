SCORING_WEIGHTS = {
    "goal": 0.55,
    "intent": 0.25,
    "rating": 0.15,
    "popularity": 0.05,
}


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
}