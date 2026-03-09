from ..utils.abs_metric import AbsMetric
from ..utils.utils import distance


class JourneyDistance(AbsMetric):
    """Computes the total distance of a journey segment."""

    @staticmethod
    def extract(uid_df, is_geo_coord):
        """Returns the cumulative distance between consecutive trace points."""
        total_distance = 0.0

        if len(uid_df) < 2:
            return total_distance

        previous_trace = uid_df.iloc[0]

        for i in range(1, len(uid_df)):
            current_trace = uid_df.iloc[i]

            first_point = {
                "lng": previous_trace["lng"],
                "lat": previous_trace["lat"],
                "alt": previous_trace["alt"],
            }
            second_point = {
                "lng": current_trace["lng"],
                "lat": current_trace["lat"],
                "alt": current_trace["alt"],
            }

            total_distance += distance(first_point, second_point, is_geo_coord)
            previous_trace = current_trace

        return total_distance
