import pandas as pd

from ..utils.abs_metric import AbsMetric


class JourneyTime(AbsMetric):
    """Computes the duration of a journey."""

    @staticmethod
    def extract(arrival_time, departure_time):
        """Returns the elapsed time between two timestamps."""
        return (
            arrival_time - departure_time
            if arrival_time > departure_time
            else pd.Timedelta(0)
        )
