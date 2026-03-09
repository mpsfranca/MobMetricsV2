from ..utils.abs_metric import AbsMetric


class TravelTime(AbsMetric):
    """Computes the total travel time of a trajectory."""

    @staticmethod
    def extract(df):
        """Returns the elapsed time between the first and last trace points."""
        start_time = df.iloc[0]["datetime"]
        end_time = df.iloc[-1]["datetime"]
        total_travel_time = end_time - start_time

        return total_travel_time.total_seconds()
