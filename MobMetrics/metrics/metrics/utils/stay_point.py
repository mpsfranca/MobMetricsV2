from .visits import Visit
from .journeys import Journey
from ...models import StayPointModel
from .utils import distance


class StayPoints:
    """Extracts stay points and related visit information from a trajectory."""

    @staticmethod
    def extract(uid, uid_df, file_name, distance_threshold, time_threshold, is_geo_coord):
        """Detects stay points for one entity and computes its journey statistics."""
        uid_df.loc[:, "spId"] = 0

        last_sp = StayPointModel.objects.filter(file_name=file_name).order_by("stay_point_id").last()
        stay_point_id = last_sp.stay_point_id + 1 if last_sp else 1

        start_idx = 0
        visit_count = 0
        time_visit_count = 0

        while start_idx < len(uid_df):
            result = StayPoints._detect_stay_point(
                uid,
                uid_df,
                start_idx,
                stay_point_id,
                is_geo_coord,
                distance_threshold,
                time_threshold,
                file_name,
            )
            if result:
                end_idx, updated_sp_id, duration, created_new = result
                uid_df.iloc[start_idx:end_idx, uid_df.columns.get_loc("spId")] = updated_sp_id
                if created_new:
                    stay_point_id += 1
                visit_count += 1
                time_visit_count += duration
                start_idx = end_idx
            else:
                start_idx += 1

        num_journeys, avg_journey_time, avg_journey_distance, avg_journey_avg_speed = Journey.process_journey(
            uid,
            uid_df,
            file_name,
            is_geo_coord,
        )

        return (
            visit_count,
            time_visit_count,
            num_journeys,
            avg_journey_time,
            avg_journey_distance,
            avg_journey_avg_speed,
        )

    @staticmethod
    def _detect_stay_point(
        uid,
        uid_df,
        start_idx,
        stay_point_id,
        is_geo_coord,
        distance_threshold,
        time_threshold,
        file_name,
    ):
        """Checks whether the segment starting at a given index forms a stay point."""
        arrival_time = uid_df.iloc[start_idx]["datetime"]
        lng_total = uid_df.iloc[start_idx]["lng"]
        lat_total = uid_df.iloc[start_idx]["lat"]
        alt_total = uid_df.iloc[start_idx]["alt"]
        point_count = 1

        end_idx = start_idx + 1
        while (
            end_idx < len(uid_df)
            and distance(uid_df.iloc[start_idx], uid_df.iloc[end_idx], is_geo_coord) <= distance_threshold
        ):
            lng_total += uid_df.iloc[end_idx]["lng"]
            lat_total += uid_df.iloc[end_idx]["lat"]
            alt_total += uid_df.iloc[end_idx]["alt"]
            point_count += 1
            end_idx += 1

        leave_time = uid_df.iloc[end_idx - 1]["datetime"]
        duration = (leave_time - arrival_time).total_seconds()

        if duration >= time_threshold:
            lng_avg = round(lng_total / point_count, 5)
            lat_avg = round(lat_total / point_count, 5)
            alt_avg = round(alt_total / point_count, 5)

            return Visit.process_visit(
                uid,
                lng_avg,
                lat_avg,
                alt_avg,
                arrival_time,
                leave_time,
                duration,
                stay_point_id,
                end_idx,
                file_name,
                is_geo_coord,
                distance_threshold,
            )

        return None
