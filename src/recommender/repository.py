import os

import psycopg


class ProductRepository:
    def __init__(self):
        self.connection = psycopg.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", "5432"),
            dbname=os.getenv("PGDATABASE", "ingredientiq"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD"),
        )

    def close(self):
        self.connection.close()

    def find_candidates(
        self,
        category=None,
        subcategory=None,
        min_price=None,
        max_price=None,
    ):
        query = """
            SELECT
                product_id,
                product_name,
                brand,
                category,
                subcategory,
                price,
                rating,
                review_count,
                loves_count
            FROM products
            WHERE 1 = 1
        """

        params = []

        if category:
            query += " AND LOWER(category) = LOWER(%s)"
            params.append(category)

        if subcategory:
            query += " AND LOWER(subcategory) = LOWER(%s)"
            params.append(subcategory)

        if min_price is not None:
            query += " AND price >= %s"
            params.append(min_price)

        if max_price is not None:
            query += " AND price <= %s"
            params.append(max_price)

        query += " ORDER BY product_id"

        with self.connection.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def get_product_ingredient_names(self, product_ids):
        if not product_ids:
            return {}

        query = """
            SELECT
                pi.product_id,
                LOWER(i.canonical_name) AS ingredient_name
            FROM product_ingredients pi
            JOIN ingredients i
                ON i.ingredient_id = pi.ingredient_id
            WHERE pi.product_id = ANY(%s)
            GROUP BY
                pi.product_id,
                LOWER(i.canonical_name)
        """

        result = {}

        with self.connection.cursor() as cur:
            cur.execute(query, (product_ids,))

            for product_id, ingredient_name in cur.fetchall():
                result.setdefault(product_id, set()).add(
                    ingredient_name
                )

        return result

    def get_goal_matches(self, product_ids, goals):
        if not product_ids or not goals:
            return {}

        query = """
            SELECT
                pi.product_id,
                LOWER(i.canonical_name) AS ingredient_name,
                LOWER(goal.value) AS goal
            FROM product_ingredients pi
            JOIN ingredients i
                ON i.ingredient_id = pi.ingredient_id
            JOIN ingredient_knowledge ik
                ON ik.ingredient_id = i.ingredient_id
            CROSS JOIN LATERAL jsonb_array_elements_text(
                ik.user_goals
            ) AS goal(value)
            WHERE pi.product_id = ANY(%s)
               AND LOWER(goal.value) = ANY(%s)
            GROUP BY
                pi.product_id,
                LOWER(i.canonical_name),
                LOWER(goal.value)
        """

        normalized_goals = [
            goal.strip().lower()
            for goal in goals
            if goal and goal.strip()
        ]

        result = {}

        with self.connection.cursor() as cur:
            cur.execute(
                query,
                (product_ids, normalized_goals),
            )

            for product_id, ingredient_name, goal in cur.fetchall():
                product_match = result.setdefault(
                    product_id,
                    {
                        "goals": set(),
                        "ingredients": set(),
                    },
                )

                product_match["goals"].add(goal)
                product_match["ingredients"].add(
                    ingredient_name
                )

        return result