from .models import RecommendationRequest

# "Fragrance-free": if the user excludes "fragrance" or "parfum", we drop every
# product that has ANY ingredient whose name contains one of these words
# (the database spells it many ways: "parfum (fragrance)", "fragrance/parfum" ...).
# Individual fragrance allergens (limonene, linalool ...) are NOT covered
# unless the user lists them by name.
FRAGRANCE_WORDS = ("fragrance", "parfum")


def normalize(value: str | None) -> str | None:
    if value is None:
        return None

    return value.strip().lower()


def has_fragrance(ingredients) -> bool:
    """True if any ingredient name contains "fragrance" or "parfum"."""
    return any(
        word in name
        for name in ingredients
        for word in FRAGRANCE_WORDS
    )


def filter_products(
    products,
    request: RecommendationRequest,
    ingredient_map,
):
    category = normalize(request.category)
    subcategory = normalize(request.subcategory)

    required = {
        normalize(name)
        for name in request.required_ingredients
    }

    excluded = {
        normalize(name)
        for name in request.excluded_ingredients
    }

    fragrance_free = any(word in excluded for word in FRAGRANCE_WORDS)

    results = []

    for product in products:
        (
            product_id,
            product_name,
            brand,
            product_category,
            product_subcategory,
            price,
            rating,
            review_count,
            loves_count,
        ) = product

        if category and normalize(product_category) != category:
            continue

        if (
            subcategory
            and normalize(product_subcategory) != subcategory
        ):
            continue

        if request.min_price is not None:
            if price is None or float(price) < request.min_price:
                continue

        if request.max_price is not None:
            if price is None or float(price) > request.max_price:
                continue

        ingredients = ingredient_map.get(product_id, set())

        if required and not required.issubset(ingredients):
            continue

        if excluded and ingredients.intersection(excluded):
            continue

        if fragrance_free and has_fragrance(ingredients):
            continue

        results.append(product)

    return results