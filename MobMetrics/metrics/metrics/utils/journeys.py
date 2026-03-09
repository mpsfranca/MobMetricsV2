from ...models import VisitModel, JourneyModel
from ..spatial.journey_distance import JourneyDistance
from ..temporal.journey_time import JourneyTime
from ..kinematic.journey_average_speed import JourneyAverageSpeed


class Journey:
    """Extracts journeys occurring between visits to stay points."""

    @staticmethod
    def process_journey(uid, uid_df, file_name, is_geo_coord):
        """Computes journey metrics for one entity and stores each detected journey."""
        if uid_df.index.name != "datetime":
            uid_df = uid_df.set_index("datetime", drop=False)

        visits = list(
            VisitModel.objects.filter(file_name=file_name, uid=uid).order_by("arv_time")
        )

        num_journeys = 0
        total_journey_time = 0
        total_journey_distance = 0
        total_journey_avg_speed = 0

        if not visits:
            return 0, 0.0, 0.0, 0.0

        first_visit = visits[0]
        journey_traces = Journey._get_traces_between(
            uid_df,
            uid_df["datetime"].min(),
            first_visit.arv_time,
        )

        if len(journey_traces) >= 2:
            num_journeys += 1
            j_time, j_dist, j_speed = Journey._create_journey(
                first_visit.uid,
                journey_traces,
                file_name,
                is_geo_coord,
            )
            total_journey_time += j_time
            total_journey_distance += j_dist
            total_journey_avg_speed += j_speed

        for i in range(len(visits) - 1):
            current_visit = visits[i]
            next_visit = visits[i + 1]

            journey_traces = Journey._get_traces_between(
                uid_df,
                current_visit.lev_time,
                next_visit.arv_time,
            )

            if len(journey_traces) >= 2:
                num_journeys += 1
                j_time, j_dist, j_speed = Journey._create_journey(
                    current_visit.uid,
                    journey_traces,
                    file_name,
                    is_geo_coord,
                )
                total_journey_time += j_time
                total_journey_distance += j_dist
                total_journey_avg_speed += j_speed

        last_visit = visits[-1]
        journey_traces = Journey._get_traces_between(
            uid_df,
            last_visit.lev_time,
            uid_df["datetime"].max(),
        )

        if len(journey_traces) >= 2:
            num_journeys += 1
            j_time, j_dist, j_speed = Journey._create_journey(
                last_visit.uid,
                journey_traces,
                file_name,
                is_geo_coord,
            )
            total_journey_time += j_time
            total_journey_distance += j_dist
            total_journey_avg_speed += j_speed

        if num_journeys == 0:
            return 0, 0.0, 0.0, 0.0

        avg_time = total_journey_time / num_journeys
        avg_distance = total_journey_distance / num_journeys
        avg_speed = total_journey_avg_speed / num_journeys

        return num_journeys, avg_time, avg_distance, avg_speed

    @staticmethod
    def _get_traces_between(uid_df, start_time, end_time):
        """Returns the trajectory segment within the specified time interval."""
        return uid_df.loc[start_time:end_time]

    @staticmethod
    def _create_journey(uid, uid_df, file_name, is_geo_coord):
        """Computes and stores the metrics of a single journey segment."""
        journey_distance = JourneyDistance.extract(uid_df, is_geo_coord)
        journey_time = JourneyTime.extract(
            uid_df["datetime"].iloc[0],
            uid_df["datetime"].iloc[-1],
        ).total_seconds()
        journey_speed = JourneyAverageSpeed.extract(journey_distance, journey_time)

        JourneyModel.objects.create(
            file_name=file_name,
            uid=uid,
            lev_id=uid_df.iloc[0]["spId"],
            arv_id=uid_df.iloc[-1]["spId"],
            journey_distance=journey_distance,
            journey_time=journey_time,
            journey_avg_speed=journey_speed,
        )

        return journey_time, journey_distance, journey_speed
