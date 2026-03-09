import tqdm

from ...models import StayPointModel
from ..utils.abs_metric import AbsMetric


class StaypointImportanceDegree(AbsMetric):
    """Computes an importance score for each stay point."""

    @staticmethod
    def extract(file_name):
        """Updates stay points with a weighted importance degree."""
        stay_points = StayPointModel.objects.filter(file_name=file_name)

        visits_list = [sp.num_visits for sp in stay_points]
        visit_time_list = [sp.total_visits_time for sp in stay_points]
        entropy_list = [sp.entropy for sp in stay_points]

        if not visits_list:
            return

        min_visits, max_visits = min(visits_list), max(visits_list)
        min_time, max_time = min(visit_time_list), max(visit_time_list)
        min_entropy, max_entropy = min(entropy_list), max(entropy_list)

        for sp in tqdm.tqdm(stay_points, desc="Stay Point Importance Degree"):
            norm_visits = StaypointImportanceDegree._normalize(sp.num_visits, min_visits, max_visits)
            norm_time = StaypointImportanceDegree._normalize(sp.total_visits_time, min_time, max_time)
            norm_entropy = StaypointImportanceDegree._normalize(sp.entropy, min_entropy, max_entropy)

            importance = (
                0.4 * norm_visits +
                0.4 * norm_time +
                0.2 * (1 - norm_entropy)
            )

            sp.importance_degree = importance
            sp.save()

    @staticmethod
    def _normalize(value, min_val, max_val):
        """Applies min-max normalization to a scalar value."""
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)
