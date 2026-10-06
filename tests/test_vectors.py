import math

import numpy as np

from src.recommender.vectors import VectorIndex, _goal_dims_from_knowledge

DIMS = ["fg_humectant", "fg_emollient", "fg_surfactant"]


def make_index():
    matrix = np.array(
        [
            [4, 0, 0],   # A: all humectant
            [40, 0, 0],  # A_long: same mix as A, ten times longer
            [2, 2, 0],   # B: half humectant, half emollient
            [0, 0, 5],   # C: all surfactant
            [0, 0, 0],   # Z: nothing known -> no vector
        ]
    )
    goal_dims = {
        "hydration": ["fg_humectant"],
        "cleansing": {"fg_surfactant": 1.0},
        "ghost": ["fg_missing"],  # points at a dimension that does not exist
    }
    return VectorIndex.from_arrays(["A", "A_long", "B", "C", "Z"], matrix, DIMS, goal_dims)


def test_cosine_similarity_values():
    sims = make_index().similarity(["hydration"], ["A", "B", "C"])

    assert math.isclose(sims["A"], 1.0, abs_tol=1e-6)
    assert math.isclose(sims["B"], math.sqrt(0.5), abs_tol=1e-6)
    assert sims["C"] == 0.0


def test_list_length_does_not_change_similarity():
    sims = make_index().similarity(["hydration"], ["A", "A_long"])

    assert math.isclose(sims["A"], sims["A_long"], abs_tol=1e-6)


def test_products_without_vector_score_zero_but_stay_in_result():
    sims = make_index().similarity(["hydration"], ["Z", "not_in_index"])

    assert sims == {"Z": 0.0, "not_in_index": 0.0}


def test_goal_names_are_case_insensitive_and_unknown_goals_ignored():
    index = make_index()

    assert index.similarity(["  HyDration "], ["A"])["A"] > 0.99
    assert index.similarity(["hydration", "no_such_goal"], ["A"]) == index.similarity(["hydration"], ["A"])


def test_no_known_goal_gives_no_goal_vector_and_zero_similarity():
    index = make_index()

    assert index.goal_vector(["no_such_goal"]) is None
    assert index.goal_vector([]) is None
    assert index.similarity(["no_such_goal"], ["A", "B"]) == {"A": 0.0, "B": 0.0}


def test_supported_goals_need_at_least_one_real_dimension():
    assert make_index().supported_goals == ["cleansing", "hydration"]


def test_several_goals_are_combined():
    sims = make_index().similarity(["hydration", "cleansing"], ["A", "C"])

    assert math.isclose(sims["A"], sims["C"], abs_tol=1e-6)
    assert math.isclose(sims["A"], math.sqrt(0.5), abs_tol=1e-6)


def test_goal_vector_has_length_one():
    vector = make_index().goal_vector(["hydration", "cleansing"])

    assert math.isclose(float(np.linalg.norm(vector)), 1.0, abs_tol=1e-6)


def test_similar_products_sorted_and_excludes_itself():
    result = make_index().similar_products("A", k=3)

    assert [pid for pid, _ in result][:2] == ["A_long", "B"]
    assert "A" not in [pid for pid, _ in result]
    scores = [score for _, score in result]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= score <= 1.0 for score in scores)


def test_similar_products_respects_k():
    assert len(make_index().similar_products("A", k=1)) == 1


def test_similar_products_empty_without_vector():
    index = make_index()

    assert index.similar_products("Z") == []
    assert index.similar_products("not_in_index") == []


def test_goal_dims_from_knowledge_keeps_jobs_most_ingredients_share():
    knowledge = [
        (["humectant"], ["hydration"]),
        (["humectant"], ["hydration"]),
        (["humectant", "amino_acid"], ["hydration"]),
        (["surfactant"], ["cleansing"]),
    ]

    dims = _goal_dims_from_knowledge(knowledge)

    assert dims["hydration"] == {"goal_hydration": 1.0, "fg_humectant": 1.0}  # amino_acid: only 1 of 3
    assert dims["cleansing"] == {"goal_cleansing": 1.0, "fg_surfactant": 1.0}
