import math

import tqdm

from ...models import StayPointModel
from ..utils.abs_metric import AbsMetric


class Entropy(AbsMetric):
    """Computes the entropy associated with each stay point."""

    @staticmethod
    def extract(total_visits, file_name):
        """Updates each stay point with its entropy value."""
        stay_points = StayPointModel.objects.filter(file_name=file_name)

        for sp in tqdm.tqdm(stay_points, desc="Stay Point Entropy"):
            probability = sp.num_visits / total_visits

            if probability > 0:
                entropy = -probability * math.log2(probability)
                sp.entropy = entropy
                sp.save()
