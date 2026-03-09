from math import log2

from ...models import QuadrantEntropyModel, GlobalMetricsModel, MetricsModel
from ..utils.abs_metric import AbsMetric


class QuadrantEntropy(AbsMetric):
    """Computes quadrant-based entropy metrics for the full trace and each entity."""

    @staticmethod
    def extract(df, quadrant_parts, file_name):
        """Computes and stores global and per-entity quadrant entropy values."""
        QuadrantEntropy._total_quadrant_entropy(df, quadrant_parts, file_name)
        QuadrantEntropy._entity_quadrant_entropy(df, quadrant_parts, file_name)

    @staticmethod
    def _total_quadrant_entropy(df, quadrant_parts, file_name):
        """Computes quadrant entropy considering all trace points together."""
        min_lng, max_lng = df["lng"].min(), df["lng"].max()
        min_lat, max_lat = df["lat"].min(), df["lat"].max()

        delta_lng = (max_lng - min_lng) / quadrant_parts
        delta_lat = (max_lat - min_lat) / quadrant_parts

        quadrant_visits = {}

        for _, row in df.iterrows():
            qlng = int((row["lng"] - min_lng) / delta_lng)
            qlat = int((row["lat"] - min_lat) / delta_lat)
            quadrant_index = (qlng, qlat)
            quadrant_visits[quadrant_index] = quadrant_visits.get(quadrant_index, 0) + 1

        total_visits = sum(quadrant_visits.values())
        occupied_quadrants = len(quadrant_visits)

        for quadrant_index, visit_count in quadrant_visits.items():
            probability = visit_count / total_visits
            entropy = -probability * log2(probability)

            QuadrantEntropyModel.objects.create(
                file_name=file_name,
                lng=quadrant_index[0],
                lat=quadrant_index[1],
                visit_count=visit_count,
                entropy=entropy,
                uid=None,
                spatial_cover=occupied_quadrants,
            )

        global_metric = GlobalMetricsModel.objects.get(file_name=file_name)
        global_metric.total_spatial_cover = occupied_quadrants
        global_metric.save()

    @staticmethod
    def _entity_quadrant_entropy(df, quadrant_parts, file_name):
        """Computes quadrant entropy separately for each entity."""
        min_lng, max_lng = df["lng"].min(), df["lng"].max()
        min_lat, max_lat = df["lat"].min(), df["lat"].max()

        delta_lng = (max_lng - min_lng) / quadrant_parts
        delta_lat = (max_lat - min_lat) / quadrant_parts

        grouped = df.groupby("uid")

        for uid, group in grouped:
            quadrant_visits = {}

            for _, row in group.iterrows():
                qlng = int((row["lng"] - min_lng) / delta_lng)
                qlat = int((row["lat"] - min_lat) / delta_lat)
                quadrant_index = (qlng, qlat)
                quadrant_visits[quadrant_index] = quadrant_visits.get(quadrant_index, 0) + 1

            total_visits = sum(quadrant_visits.values())
            occupied_quadrants = len(quadrant_visits)

            for quadrant_index, visit_count in quadrant_visits.items():
                probability = visit_count / total_visits
                entropy = -probability * log2(probability)

                QuadrantEntropyModel.objects.create(
                    file_name=file_name,
                    lng=quadrant_index[0],
                    lat=quadrant_index[1],
                    visit_count=visit_count,
                    entropy=entropy,
                    uid=uid,
                    spatial_cover=occupied_quadrants,
                )

            metric = MetricsModel.objects.get(file_name=file_name, uid=uid)
            metric.spatial_cover = occupied_quadrants
            metric.save()
