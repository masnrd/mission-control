from abc import ABC, abstractmethod
from typing import List, Tuple


class ClusterFinder(ABC):
    """DBScan Clustering Object"""
    def __init__(self, dataset):
        self.dataset = dataset  # List of points to do clustering
        self.cluster_count = 0  # Total number of clusters
        # Dictionary with keys(cluster_id), values (list of Points)
        self.clusters = {}

    @abstractmethod
    def fit(self):
        """
        Run the DBSCAN clustering algorithm.
        """
        return self.clusters

    def print_outputs(self):
        for cluster_id, points in self.clusters.items():
            points = [point.id for point in points]
            print(f"Cluster: {cluster_id}, Points: {points}")

class Cluster(ABC):
    """Generic Cluster object"""
    def __init__(self,):
        self.centre: Tuple[float, float] = (None, None)
        self.hotspots:List[Tuple[float, float]] = []
