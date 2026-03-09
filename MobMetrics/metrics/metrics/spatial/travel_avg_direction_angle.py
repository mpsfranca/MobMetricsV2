from ..utils.abs_metric import AbsMetric
from ..utils.utils import direction_angle


class TravelAvgDirectionAngle(AbsMetric):
    """Computes the average direction angle along a trajectory."""

    @staticmethod
    def extract(df, is_geo_coord):
        """Returns the mean angle between consecutive trajectory points."""
        angle_sum = 0
        count = 0

        for prev_row, curr_row in zip(df.iloc[:-1].iterrows(), df.iloc[1:].iterrows()):
            _, prev_row = prev_row
            _, curr_row = curr_row

            count += 1
            angle_sum += direction_angle(prev_row, curr_row, is_geo_coord)

        if count == 0:
            return 0.0

        return round(angle_sum / count, 5)
