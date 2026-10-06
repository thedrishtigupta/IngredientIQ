# Product vector = one number per "job" an ingredient can do (humectant, emollient, ...) or goal it serves,
# plus one for ingredients we could not classify; each number counts the product's ingredients of that kind.
# Every vector is scaled to length 1, so list length does not matter (dividing counts by the total first changes nothing).
# The "unknown" slot stops a product with 1 classified ingredient out of 30 from looking like a perfect match.
# Cosine similarity = dot product of two length-1 vectors: 1 = same mix, 0 = nothing in common. A goal is a vector too.
import numpy as np

UNKNOWN_DIM = "unknown_ingredients"
KEEP_SHARE = 0.5  # a job counts for a goal when >= half of that goal's curated ingredients do it


def _unit_rows(m):
    """Scale each row to length 1 (all-zero rows stay zero = 'no vector')."""
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return np.divide(m, norms, out=np.zeros_like(m), where=norms > 0)


class VectorIndex:
    def __init__(self, product_ids, matrix, dim_names, goal_dims):
        self._ids = list(product_ids)
        self._row = {pid: i for i, pid in enumerate(self._ids)}
        self._col = {d: i for i, d in enumerate(dim_names)}
        self._matrix = _unit_rows(np.asarray(matrix, dtype=np.float32).reshape(len(self._ids), len(self._col)))
        # goal -> {dimension name: weight}; a plain list of names means weight 1 each.
        self._goal_dims = {}
        for goal, dims in goal_dims.items():
            dims = dims if isinstance(dims, dict) else dict.fromkeys(dims, 1.0)
            dims = {d: w for d, w in dims.items() if d in self._col}
            if dims:
                self._goal_dims[goal.strip().lower()] = dims

    @classmethod
    def from_arrays(cls, product_ids, matrix, dim_names, goal_dims):
        return cls(product_ids, matrix, dim_names, goal_dims)

    @classmethod
    def from_db(cls, conn):
        rows = conn.execute("SELECT product_id, features FROM product_functional_profiles").fetchall()
        rows = [(pid, f) for pid, f in rows if f.get("mapped_ingredient_occurrences", 0) > 0]  # nothing classified = no vector
        if not rows:
            return cls([], np.zeros((0, 0)), [], {})
        # fg_* = functional groups, goal_* = user goals. fg_primary_* / goal_primary_* repeat them, so skip.
        dims = sorted(k for k in rows[0][1] if k.startswith(("fg_", "goal_")) and "_primary_" not in k)
        matrix = [[features.get(d, 0) for d in dims] + [_unknown_count(features)] for _, features in rows]
        dims.append(UNKNOWN_DIM)
        knowledge = conn.execute("SELECT functional_groups, user_goals FROM ingredient_knowledge").fetchall()
        return cls([pid for pid, _ in rows], matrix, dims, _goal_dims_from_knowledge(knowledge))

    @property
    def supported_goals(self):
        return sorted(self._goal_dims)

    def goal_vector(self, goals):
        """Length-1 vector for the goals (weights add up if several), or None if no goal maps to a dimension."""
        v = np.zeros(len(self._col), dtype=np.float32)
        for goal in goals:
            for dim, weight in self._goal_dims.get(str(goal).strip().lower(), {}).items():
                v[self._col[dim]] += weight
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else None

    def similarity(self, goals, product_ids):
        """{product_id: cosine 0..1}. Products without a vector get 0.0."""
        goal = self.goal_vector(goals)
        result = dict.fromkeys(product_ids, 0.0)
        if goal is None:
            return result
        known = [pid for pid in result if pid in self._row]
        if known:
            sims = np.clip(self._matrix[[self._row[pid] for pid in known]] @ goal, 0.0, 1.0)
            result.update(zip(known, map(float, sims)))
        return result

    def similar_products(self, product_id, k=5):
        """The k most similar other products as (product_id, cosine), best first."""
        row = self._row.get(product_id)
        if row is None or not self._matrix[row].any():
            return []
        sims = np.clip(self._matrix @ self._matrix[row], 0.0, 1.0)
        sims[row] = -1.0  # never return the product itself
        best = np.argsort(-sims, kind="stable")[:k]
        return [(self._ids[i], float(sims[i])) for i in best if sims[i] >= 0]


def _unknown_count(features):
    return features.get("total_ingredient_occurrences", 0) - features.get("mapped_ingredient_occurrences", 0)


def _goal_dims_from_knowledge(knowledge):
    """For each goal: its own goal_<goal> dimension (weight 1) + the fg_<job> dimensions
    that at least half of the goal's curated ingredients have (weight = that share)."""
    by_goal = {}  # goal -> [list of functional groups per ingredient]
    for groups, goals in knowledge:
        for goal in goals:
            by_goal.setdefault(goal, []).append(groups)
    result = {}
    for goal, ingredients in by_goal.items():
        dims = {"goal_" + goal: 1.0}
        for group in {g for groups in ingredients for g in groups}:
            share = sum(group in groups for groups in ingredients) / len(ingredients)
            if share >= KEEP_SHARE:
                dims["fg_" + group] = share
        result[goal] = dims
    return result
