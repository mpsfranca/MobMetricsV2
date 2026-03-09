import numpy as np
from math import radians, sin, cos, sqrt, atan2, degrees
from django.db.models import Avg, Sum

from ...models import (
    GlobalMetricsModel,
    MetricsModel,
    StayPointModel,
    QuadrantEntropyModel,
    ContactModel,
)


def distance(point_a, point_b, is_geo_coords):
    """Computes the 3D distance between two points."""
    if is_geo_coords:
        earth_radius = 6371000

        lat1 = radians(point_a["lat"])
        lon1 = radians(point_a["lng"])
        lat2 = radians(point_b["lat"])
        lon2 = radians(point_b["lng"])

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        horizontal_distance = earth_radius * c

        delta_alt = point_b["alt"] - point_a["alt"]
        return sqrt(horizontal_distance ** 2 + delta_alt ** 2)

    return sqrt(
        (point_b["lng"] - point_a["lng"]) ** 2 +
        (point_b["lat"] - point_a["lat"]) ** 2 +
        (point_b["alt"] - point_a["alt"]) ** 2
    )


def direction_angle(point_a, point_b, is_geo_coords):
    """Computes the horizontal movement angle between two points in degrees."""
    if is_geo_coords:
        lat1 = radians(point_a["lat"])
        lon1 = radians(point_a["lng"])
        lat2 = radians(point_b["lat"])
        lon2 = radians(point_b["lng"])

        delta_lon = lon2 - lon1

        lng = sin(delta_lon) * cos(lat2)
        lat = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)

        bearing_rad = atan2(lng, lat)
        bearing_deg = (degrees(bearing_rad) + 360) % 360

        return bearing_deg

    dx = point_b["lng"] - point_a["lng"]
    dy = point_b["lat"] - point_a["lat"]

    angle_rad = atan2(dy, dx)
    angle_deg = (degrees(angle_rad) + 360) % 360

    return angle_deg


def compute_global_metrics(file_name):
    """Aggregates and stores global metrics for a given trace file."""
    metrics_qs = MetricsModel.objects.filter(file_name=file_name)
    staypoints_qs = StayPointModel.objects.filter(file_name=file_name)
    quadrants_qs = QuadrantEntropyModel.objects.filter(file_name=file_name)
    contacts_qs = ContactModel.objects.filter(file_name=file_name)

    metrics_agg = metrics_qs.aggregate(
        avg_travel_time=Avg("travel_time"),
        avg_travel_distance=Avg("travel_distance"),
        avg_travel_avg_speed=Avg("travel_avg_speed"),
        avg_lng_center=Avg("lng_center"),
        avg_lat_center=Avg("lat_center"),
        avg_alt_center=Avg("alt_center"),
        avg_radius_of_gyration=Avg("radius_of_gyration"),
        total_num_journeys=Sum("num_journeys"),
        total_avg_journey_time=Avg("avg_journey_time"),
        total_avg_journey_distance=Avg("avg_journey_distance"),
        total_avg_journey_avg_speed=Avg("avg_journey_avg_speed"),
        avg_num_stay_points_visits=Avg("stay_points_visits"),
    )

    staypoints_agg = staypoints_qs.aggregate(
        stay_points_visits=Sum("num_visits"),
        avg_stay_point_entropy=Avg("entropy"),
    )

    quadrants_agg = quadrants_qs.aggregate(
        avg_quadrant_entropy=Avg("entropy")
    )

    label = metrics_qs.first().label if metrics_qs.exists() else ""
    num_contacts = contacts_qs.count()

    GlobalMetricsModel.objects.update_or_create(
        file_name=file_name,
        defaults={
            "label": label,
            "avg_travel_time": metrics_agg["avg_travel_time"] or 0.0,
            "avg_travel_distance": metrics_agg["avg_travel_distance"] or 0.0,
            "avg_travel_avg_speed": metrics_agg["avg_travel_avg_speed"] or 0.0,
            "avg_lng_center": metrics_agg["avg_lng_center"] or 0.0,
            "avg_lat_center": metrics_agg["avg_lat_center"] or 0.0,
            "avg_alt_center": metrics_agg["avg_alt_center"] or 0.0,
            "avg_radius_of_gyration": metrics_agg["avg_radius_of_gyration"] or 0.0,
            "total_num_journeys": metrics_agg["total_num_journeys"] or 0,
            "total_avg_journey_time": metrics_agg["total_avg_journey_time"] or 0.0,
            "total_avg_journey_distance": metrics_agg["total_avg_journey_distance"] or 0.0,
            "total_avg_journey_avg_speed": metrics_agg["total_avg_journey_avg_speed"] or 0.0,
            "avg_num_stay_points_visits": metrics_agg["avg_num_stay_points_visits"] or 0.0,
            "num_stay_points": staypoints_qs.count(),
            "stay_points_visits": staypoints_agg["stay_points_visits"] or 0,
            "avg_stay_point_entropy": staypoints_agg["avg_stay_point_entropy"] or 0.0,
            "avg_quadrant_entropy": quadrants_agg["avg_quadrant_entropy"] or 0.0,
            "num_contacts": num_contacts,
            "mobility_profile": _calculate_mobility_profile(metrics_qs),
        }
    )


def _calculate_mobility_profile(metrics_qs):
    """Computes a normalized mobility profile score from per-entity metrics."""
    vectors = []

    for metrics in metrics_qs:
        raw_values = [
            getattr(metrics, "travel_time", 0.0) or 0.0,
            getattr(metrics, "travel_distance", 0.0) or 0.0,
            getattr(metrics, "travel_avg_speed", 0.0) or 0.0,
            getattr(metrics, "num_journeys", 0.0) or 0.0,
            getattr(metrics, "avg_journey_time", 0.0) or 0.0,
            getattr(metrics, "avg_journey_distance", 0.0) or 0.0,
            getattr(metrics, "avg_journey_avg_speed", 0.0) or 0.0,
            getattr(metrics, "stay_points_visits", 0.0) or 0.0,
        ]

        min_val = min(raw_values)
        max_val = max(raw_values)

        if max_val == min_val:
            normalized = [0.0] * len(raw_values)
        else:
            normalized = [(val - min_val) / (max_val - min_val) for val in raw_values]

        vectors.append(normalized)

    if not vectors:
        return 0.0

    avg_vector = np.mean(vectors, axis=0)
    profile_score = float(np.mean(avg_vector))

    return round(profile_score, 4)
