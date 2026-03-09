from math import sqrt

from ..utils.abs_metric import AbsMetric
from ...models import MetricsModel, GlobalMetricsModel


class SpeedVariationCoefficient(AbsMetric):
    """Computes the variation coefficient of average travel speed."""

    @staticmethod
    def extract(file_name):
        """Updates the global metrics record with the speed variation coefficient."""
        metric_global = GlobalMetricsModel.objects.filter(file_name=file_name).first()

        if not metric_global:
            return

        avg_speed = metric_global.avg_travel_avg_speed

        if avg_speed == 0:
            metric_global.speed_variation_coefficient = 0
        else:
            std_dev = SpeedVariationCoefficient._standard_deviation(file_name, avg_speed)
            variation = round(std_dev / avg_speed, 5)
            metric_global.speed_variation_coefficient = variation

        metric_global.save()

    @staticmethod
    def _standard_deviation(file_name, avg_speed):
        """Computes the standard deviation of entity average speeds."""
        metrics = MetricsModel.objects.filter(file_name=file_name)

        squared_diffs = 0
        count = 0

        for metric in metrics:
            squared_diffs += (metric.travel_avg_speed - avg_speed) ** 2
            count += 1

        if count == 0:
            return 0

        return sqrt(squared_diffs / count)
