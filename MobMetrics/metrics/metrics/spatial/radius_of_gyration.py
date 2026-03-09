from math import sqrt

from ..utils.abs_metric import AbsMetric


class RadiusOfGyration(AbsMetric):
    """Computes the radius of gyration of a trajectory."""

    @staticmethod
    def extract(df, center_of_mass):
        """Returns the dispersion of trajectory points around the center of mass."""
        radius_of_gyration = 0.0

        for _, row in df.iterrows():
            lng = (row["lng"] - center_of_mass["lng_center"]) ** 2
            lat = (row["lat"] - center_of_mass["lat_center"]) ** 2
            alt = (row["alt"] - center_of_mass["alt_center"]) ** 2
            radius_of_gyration += lng + lat + alt

        radius_of_gyration = sqrt(radius_of_gyration / len(df))

        return round(radius_of_gyration, 5)
