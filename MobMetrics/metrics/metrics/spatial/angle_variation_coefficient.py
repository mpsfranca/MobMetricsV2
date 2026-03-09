from math import sqrt

from ..utils.abs_metric import AbsMetric
from ..utils.utils import direction_angle


class AngleVariationCoefficient(AbsMetric):
    """Computes the variation coefficient of movement direction angles."""

    def __init__(self, trace_file, avg_angle, parameters):
        """Initializes the metric with trajectory data and configuration values."""
        self.trace_file = trace_file
        self.avg_angle = avg_angle
        self.is_geographical_coordinates = parameters[6]

    @staticmethod
    def extract(df, avg_angle, is_geo_coord):
        """Returns the variation coefficient of trajectory direction angles."""
        standard_deviation = AngleVariationCoefficient._standard_deviation(
            df,
            avg_angle,
            is_geo_coord,
        )

        if avg_angle == 0:
            return 0.0

        return standard_deviation / avg_angle

    @staticmethod
    def _standard_deviation(df, avg_angle, is_geo_coord):
        """Computes the standard deviation of pairwise direction angles."""
        sum_squared_diffs = 0
        count = 0

        for prev_row, curr_row in zip(df.iloc[:-1].iterrows(), df.iloc[1:].iterrows()):
            _, prev_row = prev_row
            _, curr_row = curr_row

            count += 1
            angle = direction_angle(prev_row, curr_row, is_geo_coord)
            sum_squared_diffs += (angle - avg_angle) ** 2

        if count == 0:
            return 0.0

        return sqrt(sum_squared_diffs / count)
