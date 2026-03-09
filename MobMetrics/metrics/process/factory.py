"""Factory responsible for extracting and storing trace metrics."""

from tqdm import tqdm

from ..models import MetricsModel
from ..metrics.utils.stay_point import StayPoints
from ..metrics.utils.utils import compute_global_metrics
from ..metrics.temporal.travel_time import TravelTime
from ..metrics.temporal.visit_time_variation_coefficient import VisitTimeVariationCoefficient
from ..metrics.social.quadrant_entropy import QuadrantEntropy
from ..metrics.social.entropy import Entropy
from ..metrics.social.detect_contact import DetectContact
from ..metrics.spatial.angle_variation_coefficient import AngleVariationCoefficient
from ..metrics.spatial.travel_avg_direction_angle import TravelAvgDirectionAngle
from ..metrics.spatial.travel_distance import TravelDistance
from ..metrics.utils.center_of_mass import CenterOfMass
from ..metrics.spatial.radius_of_gyration import RadiusOfGyration
from ..metrics.spatial.trajectory_correlation import TrajectoryCorrelationDegree
from ..metrics.spatial.staypoint_importance_degree import StaypointImportanceDegree
from ..metrics.kinematic.travel_average_speed import TravelAverageSpeed
from ..metrics.kinematic.speed_variation_coefficient import SpeedVariationCoefficient


class Factory:
    """Coordinates per-entity extraction and global metric aggregation."""

    @staticmethod
    def extract(data, df):
        """Extracts metrics from the full trace dataset."""
        total_visits = 0
        groups = df.groupby("uid")

        for uid, uid_df in tqdm(groups, total=groups.ngroups, desc="Proccessing individual metrics..."):
            uid_df = uid_df.sort_values("datetime")
            Factory._metrics(uid, uid_df, data)
            total_visits += Factory._stayPoint(
                uid,
                uid_df,
                data["name"],
                data["distance_threshold"],
                data["time_threshold"],
                data["is_geo_coord"],
            )

        # These metrics depend on previously stored per-entity or stay-point results.
        Entropy.extract(total_visits, data["name"])
        StaypointImportanceDegree.extract(data["name"])

        if not data["skip_contact_detection"]:
            DetectContact.extract(
                df,
                data["name"],
                data["radius_threshold"],
                data["contact_time_threshold"],
                data["is_geo_coord"],
            )

        compute_global_metrics(data["name"])
        QuadrantEntropy.extract(df, data["quadrant_parts"], data["name"])
        TrajectoryCorrelationDegree.extract(df, data["name"])
        VisitTimeVariationCoefficient.extract(data["name"])
        SpeedVariationCoefficient.extract(data["name"])

    @staticmethod
    def _metrics(uid, uid_df, data):
        """Computes and stores base metrics for a single entity."""
        travel_time = TravelTime.extract(uid_df)
        travel_distance = TravelDistance.extract(uid_df, data["is_geo_coord"])
        travel_avg_speed = TravelAverageSpeed.extract(travel_distance, travel_time)
        center_of_mass = CenterOfMass.extract(uid_df)
        radius_of_gyration = RadiusOfGyration.extract(uid_df, center_of_mass)
        avg_direction_angle = TravelAvgDirectionAngle.extract(uid_df, data["is_geo_coord"])
        angle_variation_coefficient = AngleVariationCoefficient.extract(
            uid_df,
            avg_direction_angle,
            data["is_geo_coord"],
        )

        MetricsModel.objects.create(
            file_name=data["name"],
            label=data["label"],
            uid=uid,
            lng_center=center_of_mass["lng_center"],
            lat_center=center_of_mass["lat_center"],
            alt_center=center_of_mass["alt_center"],
            travel_time=travel_time,
            travel_distance=travel_distance,
            travel_avg_speed=travel_avg_speed,
            travel_avg_angle_direction=avg_direction_angle,
            radius_of_gyration=radius_of_gyration,
            angle_variation_coefficient=angle_variation_coefficient,
        )

    @staticmethod
    def _stayPoint(uid, uid_df, file_name, distance_threshold, time_threshold, is_geo_coord):
        """Extracts stay-point metrics for a single entity and updates its record."""
        (
            visit_count,
            time_visit_count,
            num_journeys,
            avg_journey_time,
            avg_journey_distance,
            avg_journey_avg_speed,
        ) = StayPoints.extract(
            uid,
            uid_df,
            file_name,
            distance_threshold,
            time_threshold,
            is_geo_coord,
        )

        metric = MetricsModel.objects.get(file_name=file_name, uid=uid)

        metric.stay_points_visits = visit_count
        metric.avg_time_visit = time_visit_count / visit_count if visit_count != 0 else 0
        metric.num_journeys = num_journeys
        metric.avg_journey_time = avg_journey_time
        metric.avg_journey_distance = avg_journey_distance
        metric.avg_journey_avg_speed = avg_journey_avg_speed

        metric.save()

        return visit_count
