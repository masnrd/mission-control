import numpy as np
import folium
from scipy.stats import multivariate_normal
from typing import List, Tuple
import h3

from pathfinder.pathfinder import BayesianHexSearch, init_empty_prob_map, update_prob_map_w_hotspots, update_probability_map
from maplib import LatLon

# Constants
N_RINGS_CLUSTER = 50
DEFAULT_RESOLUTION = 14
MAX_NUMBER_STEPS = 3000  # Assuming a maximum number of steps to take
START_TUPLE = (1.34254, 103.96381)
PROBABILITY_DECAY = 0.95
N_DRONES = 4  # Number of drones
N_TRIALS = 100

boundary_pts = [
    (1.34554, 103.95949),
    (1.34552, 103.96812),
    (1.33954, 103.96831),
    (1.33964, 103.95952),
]

hotspots = [
    (1.3408531, 103.9611108),
    (1.3409068, 103.9621181),
    (1.3402594, 103.9621944),
    (1.3447965, 103.9637608),
    (1.3418683, 103.9650483),
    (1.3411711, 103.9653916),
    (1.3443996, 103.9603276),
    (1.3443996, 103.9648981),
    (1.3433592, 103.9626021),
    (1.3450968, 103.9611108)
]

# Function to generate victims around hotspots using Gaussian distribution
def generate_victims(n_victims: int, hotspots: List[Tuple[float, float]], boundary_pts: List[Tuple[float, float]]):
    hotspots_np = np.array(hotspots)
    boundary_pts_np = np.array(boundary_pts)
    
    grid_x, grid_y = np.mgrid[1.33964:1.34552:100j, 103.95949:103.96831:100j]
    pos = np.dstack((grid_x, grid_y))
    combined_pdf = np.zeros(pos.shape[:2])
    covariance_matrix = [[0.00000001, 0], [0, 0.00000001]]
    
    for hotspot in hotspots:
        rv = multivariate_normal(hotspot, covariance_matrix)
        combined_pdf += rv.pdf(pos)
    
    combined_pdf /= np.sum(combined_pdf)
    
    victim_indices = np.random.choice(np.arange(combined_pdf.size), p=combined_pdf.ravel(), size=n_victims)
    victim_coords = np.column_stack(np.unravel_index(victim_indices, combined_pdf.shape))
    victims = np.column_stack((grid_x[victim_coords[:, 0], victim_coords[:, 1]], grid_y[victim_coords[:, 0], victim_coords[:, 1]]))

    return victims

# Function to create a zigzag path
def create_zigzag_path(hexagons, hex_centers):
    rows = {}
    for hex in hexagons:
        lat = round(hex_centers[hex][0], 6)
        if lat not in rows:
            rows[lat] = []
        rows[lat].append(hex)
    
    zigzag_path = []
    toggle = False
    for lat in sorted(rows.keys()):
        row = rows[lat]
        if toggle:
            zigzag_path.extend(reversed(row))
        else:
            zigzag_path.extend(row)
        toggle = not toggle

    return zigzag_path

# Function to run the zigzag search
def run_zigzag_search(boundary_pts: List[Tuple[float, float]], victim_hexagons: List[str], n_drones: int):
    
    polygon = {
        'type': 'Polygon',
        'coordinates': [[
            [lng, lat] for lat, lng in boundary_pts
        ]]
    }
    
    hexagons = list(h3.polyfill(polygon, DEFAULT_RESOLUTION, geo_json_conformant=True))
    hex_centers = {h: h3.h3_to_geo(h) for h in hexagons}
    sorted_hexagons = sorted(hexagons, key=lambda h: (hex_centers[h][0], hex_centers[h][1]))
    zigzag_path = create_zigzag_path(sorted_hexagons, hex_centers)
    
    detected_history_base = {}
    
    for i in range(len(zigzag_path)):
        for j in range(len(victim_hexagons)):
            if victim_hexagons[j] == zigzag_path[i] and j not in detected_history_base:
                detected_history_base[j] = i
    detected_divided = [step % (len(zigzag_path) / n_drones) for step in detected_history_base.values()]
    metrics = {
        'total_steps': len(zigzag_path),
        'average_steps_per_drone': len(zigzag_path) / n_drones,
        'victims_found': len(detected_history_base),
        'average_steps_to_find_victims': sum(detected_divided) / len(detected_divided) if len(detected_divided) > 0 else 100000000000
    }
    
    return metrics

# Function to run the pathfinder search (assumed implementation)
def run_pathfinder_search(boundary_pts: List[Tuple[float, float]], victim_hexagons: List[str], hotspots: List[Tuple[float, float]], n_drones: int):
    # Assumes the presence of pathfinder logic to be implemented
    # Placeholder for the actual pathfinder logic
    CLUSTER_THRESHOLD = 0.1
    N_RINGS_CLUSTER = 50
    DEFAULT_RESOLUTION = 14
    MAX_NUMBER_STEPS = 3000  # Assuming a maximum number of steps to take
    START_TUPLE = np.mean(boundary_pts, axis=0)

    START_TUPLE = np.mean(boundary_pts, axis=0)

    from run_clustering import run_clustering

    clusters = run_clustering(hotspots, threshold=CLUSTER_THRESHOLD)
    clusters = list(clusters.values())
    clusters = sorted(clusters, key=lambda x:len(x[1]), reverse=False)

    available_drones = [i for i in range(n_drones)]
    step_count = [0 for _ in range(4)]
    drone_current_pos = [START_TUPLE for _ in range(4)]
    detected_history = {}

    while len(clusters) > 0:

        c = clusters.pop() # [0] is location of cluster, [1] is list of hotspots

        drone = available_drones.index(step_count.index(min(step_count))) # Take the drone with minimum number of steps

        # Explore using drone
        # Go to cluster center
        path_to_cluster_centre = h3.h3_line(h3.geo_to_h3(drone_current_pos[drone][0], drone_current_pos[drone][1], DEFAULT_RESOLUTION),
                                            h3.geo_to_h3(c[0][0], c[0][1], DEFAULT_RESOLUTION))
        step_count[drone] += len(path_to_cluster_centre) - 1 # not inclusive of current cell
        drone_current_pos[drone] = (c[0][0], c[0][1])

        # Initialize probability map
        target_pos = c[0]
        target_pos_latlon = LatLon(target_pos[0], target_pos[1])
        prob_map = init_empty_prob_map(target_pos_latlon, N_RINGS_CLUSTER)
        prob_map = update_prob_map_w_hotspots(probability_map=prob_map, hotspots=c[1])
        # hotspots = cluster[1]

        # # Initialize pathfinder
        pathfinder = BayesianHexSearch(DEFAULT_RESOLUTION, center=target_pos)

        path = []
        for i in range(MAX_NUMBER_STEPS):
            drone_current_pos[drone] = pathfinder.find_next_step(drone_current_pos[drone], prob_map)
            prob_map = update_probability_map(prob_map, drone_current_pos[drone], PROBABILITY_DECAY)
            if i%100==0: path.append(drone_current_pos[drone])
            step_count[drone] += 1

            for j in range(len(victim_hexagons)):
                if victim_hexagons[j] == h3.geo_to_h3(drone_current_pos[drone][0], drone_current_pos[drone][1], DEFAULT_RESOLUTION) and j not in detected_history:
                    detected_history[j] = step_count[drone]

    metrics = {
        'total_steps': sum(step_count),
        'average_steps_per_drone': sum(step_count)/len(step_count),
        'victims_found': len(detected_history),
        'average_steps_to_find_victims': sum(list(detected_history.values()))/len(detected_history) if len(detected_history) > 0 else 100000000000
    }
    return metrics

# Function to run experiments and collect metrics
def run_experiments(boundary_pts: List[Tuple[float, float]], hotspots: List[Tuple[float, float]], n_trials: int, n_victims: int, n_drones: int):
    zigzag_metrics = []
    pathfinder_metrics = []
    
    for i in range(n_trials):
        print(f'Starting trial {i}...')
        victims = generate_victims(n_victims, hotspots, boundary_pts)
        victim_hexagons = [h3.geo_to_h3(victim[0], victim[1], DEFAULT_RESOLUTION) for victim in victims]
        print(f'| Zigzag')
        zigzag_metrics.append(run_zigzag_search(boundary_pts, victim_hexagons, n_drones))
        print(f'| Probability')
        pathfinder_metrics.append(run_pathfinder_search(boundary_pts, victim_hexagons, hotspots, n_drones))
        print("\n\n")
    
    return zigzag_metrics, pathfinder_metrics

# Function to calculate average metrics
def calculate_average_metrics(metrics_list: List[dict]):
    avg_metrics = {
        'total_steps': np.mean([m['total_steps'] for m in metrics_list]),
        'average_steps_per_drone': np.mean([m['average_steps_per_drone'] for m in metrics_list]),
        'victims_found': np.mean([m['victims_found'] for m in metrics_list]),
        'average_steps_to_find_victims': np.mean([m['average_steps_to_find_victims'] for m in metrics_list])
    }
    return avg_metrics

# Run experiments
n_victims = 15
zigzag_metrics, pathfinder_metrics = run_experiments(boundary_pts, hotspots, N_TRIALS, n_victims, N_DRONES)

print("Zigzag:", zigzag_metrics)
print("Pathfinder:", pathfinder_metrics)
print("\n\n")

# Calculate average metrics
avg_zigzag_metrics = calculate_average_metrics(zigzag_metrics)
avg_pathfinder_metrics = calculate_average_metrics(pathfinder_metrics)

print("Zigzag Search Average Metrics:", avg_zigzag_metrics)
print("Pathfinder Search Average Metrics:", avg_pathfinder_metrics)



