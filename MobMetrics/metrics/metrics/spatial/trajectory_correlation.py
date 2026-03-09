import numpy as np

import tqdm
from sklearn.metrics.pairwise import cosine_similarity

from ..utils.abs_metric import AbsMetric
from ...models import GlobalMetricsModel


class TrajectoryCorrelationDegree(AbsMetric):
    """Computes a global trajectory correlation score from pairwise similarity."""

    @staticmethod
    def extract(df, file_name):
        """Samples trajectories, computes their similarity, and stores the result."""
        vectors = []
        fraction = 0.8
        min_points = 20

        group_sizes = df.groupby("uid").size()
        fixed_n_points = max(min_points, int(fraction * group_sizes.min()))

        for _, df_ent in tqdm.tqdm(df.groupby("uid"), desc="Trajectory Correlation Degree"):
            traj_vector = TrajectoryCorrelationDegree._uniform_sample_traj(df_ent, fixed_n_points)

            if traj_vector is not None:
                vectors.append(traj_vector)

        if len(vectors) < 2:
            return 0.0

        vectors = np.array(vectors)
        sim_matrix = cosine_similarity(vectors)

        upper_indices = np.triu_indices_from(sim_matrix, k=1)
        sim_values = sim_matrix[upper_indices]

        dist_values = 1 - sim_values
        correlation_degree = 1 - np.std(dist_values)

        global_metric = GlobalMetricsModel.objects.get(file_name=file_name)
        global_metric.trajectory_correlation = correlation_degree
        global_metric.save()

    @staticmethod
    def _uniform_sample_traj(uid_df, fixed_n_points):
        """Uniformly samples a trajectory and converts it to a flat coordinate vector."""
        uid_df_sorted = uid_df.sort_values("datetime")

        if len(uid_df_sorted) < fixed_n_points:
            return None

        sampled = uid_df_sorted.iloc[
            np.linspace(0, len(uid_df_sorted) - 1, fixed_n_points, dtype=int)
        ]

        return sampled[["lng", "lat"]].to_numpy().flatten()
