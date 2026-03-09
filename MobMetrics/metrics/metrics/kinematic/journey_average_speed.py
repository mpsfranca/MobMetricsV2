from ..utils.abs_metric import AbsMetric


class JourneyAverageSpeed(AbsMetric):
    """Computes the average speed of a journey."""

    @staticmethod
    def extract(distance, time):
        """Returns the average speed, or zero when the duration is zero."""
        return distance / time if time > 0 else 0
