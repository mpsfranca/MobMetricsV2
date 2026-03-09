from math import sqrt

from ..utils.abs_metric import AbsMetric
from ...models import MetricsModel, VisitModel


class VisitTimeVariationCoefficient(AbsMetric):
    """Computes the variation coefficient of visit durations for each entity."""

    @staticmethod
    def extract(file_name):
        """Updates each entity with the coefficient of variation of its visit times."""
        metrics = MetricsModel.objects.filter(file_name=file_name)

        for metric in metrics:
            metric_id = metric.uid
            metric_avg_time_visit = metric.avg_time_visit

            visits = VisitModel.objects.filter(
                file_name=file_name,
                uid=metric_id,
            )

            deviation_sum = 0
            num_visits = 0

            for visit in visits:
                num_visits += 1
                deviation_sum += (visit.visit_time - metric_avg_time_visit) ** 2

            if num_visits > 0 and metric_avg_time_visit != 0:
                standard_deviation = sqrt(deviation_sum / num_visits)
                visit_time_variation_coefficient = standard_deviation / metric_avg_time_visit
                metric.visit_time_variation_coefficient = visit_time_variation_coefficient
                metric.save()
