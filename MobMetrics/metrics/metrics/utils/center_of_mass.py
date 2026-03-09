from .abs_metric import AbsMetric


class CenterOfMass(AbsMetric):
    """Computes the center of mass of a trajectory."""

    @staticmethod
    def extract(df):
        """Returns the average longitude, latitude, and altitude."""
        lng, lat, alt = 0, 0, 0

        for _, row in df.iterrows():
            lng += row["lng"]
            lat += row["lat"]
            alt += row["alt"]

        num_points = len(df)

        lng_center = lng / num_points
        lat_center = lat / num_points
        alt_center = alt / num_points

        return {
            "lng_center": round(lng_center, 5),
            "lat_center": round(lat_center, 5),
            "alt_center": round(alt_center, 5),
        }
