from .utils import distance
from ...models import StayPointModel, VisitModel


class Visit:
    """Handles visit registration and stay-point reuse."""

    @staticmethod
    def process_visit(
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
    ):
        """Associates a visit with an existing stay point or creates a new one."""
        for existing_sp in StayPointModel.objects.filter(file_name=file_name):
            dist = distance(
                {"lng": existing_sp.lng_center, "lat": existing_sp.lat_center, "alt": existing_sp.alt_center},
                {"lng": lng_avg, "lat": lat_avg, "alt": alt_avg},
                is_geo_coord,
            )

            if dist <= distance_threshold:
                existing_sp.num_visits += 1
                existing_sp.total_visits_time += duration
                existing_sp.save()

                VisitModel.objects.create(
                    file_name=file_name,
                    uid=uid,
                    stay_point_id=existing_sp.stay_point_id,
                    arv_time=arrival_time,
                    lev_time=leave_time,
                    visit_time=duration,
                )

                return end_idx, existing_sp.stay_point_id, duration, False

        # No compatible stay point was found for this visit.
        StayPointModel.objects.create(
            file_name=file_name,
            stay_point_id=stay_point_id,
            lng_center=lng_avg,
            lat_center=lat_avg,
            alt_center=alt_avg,
            num_visits=1,
            total_visits_time=duration,
        )

        VisitModel.objects.create(
            file_name=file_name,
            uid=uid,
            stay_point_id=stay_point_id,
            arv_time=arrival_time,
            lev_time=leave_time,
            visit_time=duration,
        )

        return end_idx, stay_point_id, duration, True
