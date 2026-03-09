from ..utils.abs_metric import AbsMetric
from ..utils.utils import distance


class TravelDistance(AbsMetric):
    """Computes the total traveled distance of a trajectory."""

    @staticmethod
    def extract(df, is_geo_coord):
        """Returns the sum of distances between consecutive trajectory points."""
        travel_distance = 0.0

        for prev_row, curr_row in zip(df.iloc[:-1].iterrows(), df.iloc[1:].iterrows()):
            _, prev_row = prev_row
            _, curr_row = curr_row

            travel_distance += distance(prev_row, curr_row, is_geo_coord)

        return round(travel_distance, 5)
