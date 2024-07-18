import numpy as np
from typing import Dict, List, Set, Tuple

from clusterfinder.point import Point
from clusterfinder.clusterfinder import DIANAClusterFinder


def run_clustering(hotspots_locations: List[Tuple], threshold=0.1) -> Dict[int, object]:
    '''Returns a dictionary of cluster_id : Tuple(centre, List(Cluster))'''
    if len(hotspots_locations) == 0: return {}
    hotspots = [Point(id, h) for id, h in enumerate(hotspots_locations)]

    # Find clusters
    cluster_finder = DIANAClusterFinder(hotspots, threshold=threshold)
    cluster_results = cluster_finder.fit() #cluster_results: Dict[int, List[Tuple[float,float]]]

    # Sort by most hotspots:
    sorted_clusters = {
        k: v for k, v in sorted(cluster_results.items(), key=lambda item: len(item[1]), reverse=True)
    }
    cluster_results = sorted_clusters

    # Find cluster centers
    all_centres = dict()

    idx = 0
    for _, hotspots in cluster_results.items():
        centre, _ = find_search_centre(hotspots)
        all_centres[idx] = (centre, [(hotspot.latlon.lat, hotspot.latlon.lon) for hotspot in hotspots])
        idx += 1

    return all_centres


def find_search_centre(cluster: List[Point]) -> Tuple[Tuple[float, float], float]:
    """
    Find the geographic center of a cluster of Points and the maximum distance from the centre to a point.

    :param cluster: A list of Point objects.
    :return: A tuple containing:
             - A tuple representing the geographic center of the cluster (latitude, longitude).
             - The maximum distance from the centre to a point in the cluster. (in m)
    """

    if not cluster:
        raise ValueError("The cluster is empty")

    # Convert all points to Cartesian coordinates
    x, y, z = 0.0, 0.0, 0.0

    for point in cluster:
        latitude = np.radians(point.coordinates[0])
        longitude = np.radians(point.coordinates[1])

        x += np.cos(latitude) * np.cos(longitude)
        y += np.cos(latitude) * np.sin(longitude)
        z += np.sin(latitude)

    # Compute average coordinates
    total_points = len(cluster)
    x /= total_points
    y /= total_points
    z /= total_points

    # Convert average coordinates back to latitude and longitude
    central_longitude = np.arctan2(y, x)
    central_square_root = np.sqrt(x * x + y * y)
    central_latitude = np.arctan2(z, central_square_root)

    # Convert radians back to degrees
    central_latitude = np.degrees(central_latitude)
    central_longitude = np.degrees(central_longitude)

    centre_point = Point(-99, (central_latitude, central_longitude))

    # Calculate the maximum distance
    max_distance = 0
    for point in cluster:
        max_distance = max(max_distance, point.distance(centre_point))

    return centre_point.coordinates, max_distance*1000
