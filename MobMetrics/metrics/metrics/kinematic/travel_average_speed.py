from ..utils.abs_metric import AbsMetric


class TravelAverageSpeed(AbsMetric):
    """Computes the average speed over the full trajectory."""

    @staticmethod
    def extract(travel_distance, travel_time):
        """Returns the average speed rounded to five decimal places."""
        if travel_time != 0.0:
            average_speed = travel_distance / travel_time
        else:
            average_speed = 0

        return round(average_speed, 5)
