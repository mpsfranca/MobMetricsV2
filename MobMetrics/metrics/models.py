"""Django models for trace data, configuration, and derived mobility metrics."""

from django.db import models


class ConfigModel(models.Model):
    """Stores configuration parameters used during data processing."""
    
    file_name = models.TextField()
    label = models.TextField()
    is_geo_coord = models.BooleanField()

    distance_threshold = models.FloatField()
    time_threshold = models.FloatField()

    radius_threshold = models.FloatField()
    quadrant_parts = models.FloatField()

    def __str__(self) -> str:
        return f"{self.file_name} - {self.label}"


class MetricsModel(models.Model):
    """Stores computed metrics for an individual entity."""
    
    file_name = models.TextField()
    label = models.TextField()
    uid = models.IntegerField()

    lng_center = models.FloatField()
    lat_center = models.FloatField()
    alt_center = models.FloatField()

    travel_time = models.FloatField()
    travel_distance = models.FloatField()
    travel_avg_speed = models.FloatField()
    travel_avg_angle_direction = models.FloatField()
    radius_of_gyration = models.FloatField()
    spatial_cover = models.IntegerField(null=True, blank=True)

    total_contact_time = models.FloatField(default=0)
    num_contacts = models.FloatField(default=0)
    avg_contact_time = models.FloatField(default=0)

    angle_variation_coefficient = models.FloatField()

    stay_points_visits = models.IntegerField(null=True, blank=True)
    avg_time_visit = models.FloatField(null=True, blank=True)
    visit_time_variation_coefficient = models.FloatField(null=True, blank=True)

    num_journeys = models.IntegerField(null=True, blank=True)
    avg_journey_time = models.FloatField(null=True, blank=True)
    avg_journey_distance = models.FloatField(null=True, blank=True)
    avg_journey_avg_speed = models.FloatField(null=True, blank=True)


class GlobalMetricsModel(models.Model):
    """Stores aggregate metrics computed for an entire trace."""

    file_name = models.TextField()
    label = models.TextField()

    avg_lng_center = models.FloatField()
    avg_lat_center = models.FloatField()
    avg_alt_center = models.FloatField()

    avg_travel_time = models.FloatField()
    avg_travel_distance = models.FloatField()
    avg_travel_avg_speed = models.FloatField()
    avg_radius_of_gyration = models.FloatField()

    num_stay_points = models.IntegerField()
    avg_num_stay_points_visits = models.FloatField()
    stay_points_visits = models.IntegerField()
    avg_stay_point_entropy = models.FloatField()

    avg_quadrant_entropy = models.FloatField()
    num_contacts = models.IntegerField()

    total_num_journeys = models.IntegerField()
    total_avg_journey_time = models.FloatField()
    total_avg_journey_distance = models.FloatField()
    total_avg_journey_avg_speed = models.FloatField()

    trajectory_correlation = models.FloatField(null=True, blank=True)
    total_spatial_cover = models.IntegerField(null=True, blank=True)
    mobility_profile = models.FloatField(null=True, blank=True)

    speed_variation_coefficient = models.FloatField(null=True, blank=True)


class StayPointModel(models.Model):
    """Stores detected stay points and their associated metrics."""

    file_name = models.TextField()

    stay_point_id = models.IntegerField()
    lng_center = models.FloatField()
    lat_center = models.FloatField()
    alt_center = models.FloatField()

    num_visits = models.IntegerField()
    total_visits_time = models.FloatField(null=True, blank=True)
    entropy = models.FloatField(null=True, blank=True)
    importance_degree = models.FloatField(null=True, blank=True)


class JourneyModel(models.Model):
    """Stores journeys performed between stay points."""

    file_name = models.TextField()
    uid = models.IntegerField()

    # Identifier of the stay point where the entity departed.
    lev_id = models.IntegerField()

    # Identifier of the stay point where the entity arrived.
    arv_id = models.IntegerField()

    journey_time = models.FloatField()
    journey_distance = models.FloatField()
    journey_avg_speed = models.FloatField()


class VisitModel(models.Model):
    """Stores visits of entities to stay points."""

    file_name = models.TextField()
    uid = models.IntegerField()

    stay_point_id = models.IntegerField()
    arv_time = models.DateTimeField()
    lev_time = models.DateTimeField()
    visit_time = models.FloatField()


class ContactModel(models.Model):
    """Stores contact events detected between two entities."""

    file_name = models.TextField()

    id1 = models.IntegerField()
    id2 = models.IntegerField()

    initial_timestamp = models.DateTimeField()
    final_timestamp = models.DateTimeField()
    contact_time = models.FloatField()


class QuadrantEntropyModel(models.Model):
    """Stores entropy-related measurements for spatial quadrants."""

    file_name = models.TextField()

    # Null indicates that the value refers to the full trace.
    uid = models.IntegerField(null=True, blank=True)

    lng = models.IntegerField()
    lat = models.IntegerField()

    visit_count = models.IntegerField()
    entropy = models.FloatField()
    spatial_cover = models.IntegerField(null=True)


class TraceModel(models.Model):
    """Stores raw spatiotemporal points from trace files."""

    file_name = models.TextField()
    uid = models.IntegerField()

    lng = models.FloatField()
    lat = models.FloatField()
    alt = models.FloatField()

    datetime = models.DateTimeField()
