from .models import RecommendationRequest


def normalize(value: str | None) -> str | None:
    if value is None:
        return None

    return value.strip().lower()


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

        results.append(product)

    return results