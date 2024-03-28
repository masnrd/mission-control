"""
pathfinder:
Pathfinding algorithm for the drone

NOTICE for Pathfinding team:
- I renamed all instances of 'center' to 'centre', and 'centre_hexagon' to 'centre_hex'
- Currently, `None` is passed to `prob_map`, so an error could occur if the code relies on it.
"""
from threading import Thread
import h3
import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Dict, NewType
from maplib import LatLon
import copy
from pathfinder.utils import *

DEFAULT_RESOLUTION = 14
N_RINGS_CLUSTER = 20     # Defines the number of rings in a cluster by default
PROBABILITY_DECAY=0.3

# Probability Map type definition: A dictionary, where each H3 hexagon index is mapped to a specific probability.
ProbabilityMap = NewType("ProbabilityMap", Dict[str, float])

def update_prob_map_w_hotspots(probability_map: ProbabilityMap, hotspots: Tuple[float, float],
        sigma: float = 0.003, r_range: int = 100) -> ProbabilityMap:
    """
    Update the probability map based on a given hotspot.

    Parameters:
    - prob_en: numpy array representing the probability map
    - hotspot: tuple containing latitude and longitude of the hotspot
    - sigma: standard deviation for the gaussian probability distribution
    - r_range: range for hex_ring (default is 100)

    Returns:
    - Updated prob_en
    """
    def gaussian_probability(dist, sig=0.3):
        return np.exp(-dist**2 / (2 * sig**2))

    def euclidean(point1, point2):
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    delta_probability_map = {}
    for hotspot in hotspots:
        hex_hotspot = h3.geo_to_h3(hotspot[0], hotspot[1], DEFAULT_RESOLUTION)

        #NOTE: Sanity check to see if hex_hotspot being added to the map is within the map size
        if hex_hotspot not in probability_map: print(f'Hex hotspot {hex_hotspot} not in prob_map')

        for i in range(0, r_range):
            hex_at_r = h3.hex_ring(hex_hotspot, i)
            if hex_at_r:  # Checking if hex_at_r is not empty
                distance = euclidean(h3.h3_to_geo(hex_hotspot),
                                     h3.h3_to_geo(next(iter(hex_at_r))))
                probability = gaussian_probability(distance, sigma)
                for hex_idx in hex_at_r:
                    if hex_idx in probability_map:
                        delta_probability_map[hex_idx] = probability + delta_probability_map.get(hex_idx, 0)
                    else:
                        print("Not in prob_map")
                        pass
    # Normalize the delta_probability_map
    total_delta_prob = sum(delta_probability_map.values())
    if total_delta_prob != 0:
        delta_probability_map = {key: (value / total_delta_prob) for key, value in delta_probability_map.items()}
    # Update the original probability map with the delta_probability_map
    for hex_idx, value in delta_probability_map.items():
        if hex_idx in probability_map:
            probability_map[hex_idx] += value
        else:
            print("Delta not in original prob")
            pass
    # Normalize the updated probability map
    total_prob = sum(probability_map.values())
    if total_prob != 0:
        probability_map = {key: (value / total_prob) for key, value in probability_map.items()}
    else:
        print("Entire probability map is zero")

    return probability_map

def init_empty_prob_map(centre_pos: LatLon, n_rings: int) -> ProbabilityMap:
    """
    Initialises an empty probability map.
    - `centre_pos`: Centre of the probability map.
    - `n_rings`: Number of rings around the centre hexagon.
    """
    prob_map = {}
    h3_indices = h3.k_ring(
        h3.geo_to_h3(centre_pos.lat, centre_pos.lon, DEFAULT_RESOLUTION),
        n_rings,
    )

    for h3_index in h3_indices:
        prob_map[h3_index] = 0
    
    return prob_map

def update_probability_map( probability_map: dict[str, float], centre: tuple[float, float], f: float) -> dict[str, float]:
    """Update the probability map using Bayes theorem.

    Args:
        :param f: Probability of finding a person
        :param centre:
        :param probability_map:
    """
    hex_centre = h3.geo_to_h3(
        centre[0], centre[1], DEFAULT_RESOLUTION)
    
    if hex_centre not in probability_map: 
        print("Has not reached cluster hex map yet") 
        return # When it is traveling to prob map

    # Prior
    prior = probability_map[hex_centre]

    # Posterior
    posterior = prior*(1-f) / (1-prior*f)
    sum_before_update = sum(probability_map.values())

    probability_map[hex_centre] = posterior

    # Distribute
    sum_after_update = sum(probability_map.values())
    if sum_after_update != 0:
        probability_map = {
            key: value / sum_after_update for key, value in probability_map.items()}
        return probability_map
    else:
        print("Entire probability map is zero")
        return dict()

class PathfinderState:
    """ Pathfinding state utilised by the drone. """
    def __init__(self, start_pos: LatLon, prob_map: ProbabilityMap = None):
        self.max_step = 300
        self.step_count = 0
        self.simulated_path = None
        start_tup = (start_pos.lat, start_pos.lon)
        self._pathfinder = BayesianHexSearch(DEFAULT_RESOLUTION, start_tup)  #TODO: to be set by the caller, based on the search method defined by MC
        self._pathfinder_sim = BayesianHexSearch(DEFAULT_RESOLUTION, start_tup)
        self._prob_map = prob_map
        if self.simulated_path is None:
            self.simulated_path = self.get_simulated_path(start_pos)

    def get_next_waypoint(self, cur_pos: LatLon) -> LatLon:
        self.step_count += 1
        if self.step_count > self.max_step:
            return None

        cur_tup = (cur_pos.lat, cur_pos.lon)
        next_tup = self._pathfinder.find_next_step(cur_tup, self._prob_map)
        self._prob_map = update_probability_map(self._prob_map, next_tup, PROBABILITY_DECAY)
        return LatLon(next_tup[0], next_tup[1])

    def get_simulated_path(self, cur_pos: LatLon) -> Dict[int, Dict]:
        sim_map = copy.deepcopy(self._prob_map)
        step = 0
        simulated_path = dict()

        while step < self.max_step:
            cur_tup = (cur_pos.lat, cur_pos.lon)
            next_tup = self._pathfinder_sim.find_next_step(cur_tup, sim_map)

            sim_map = update_probability_map(sim_map, next_tup, PROBABILITY_DECAY)
            cur_pos = LatLon(next_tup[0], next_tup[1])
            simulated_path[step] = cur_pos.to_dict()
            step += 1

        return simulated_path

    def found_signals(self, cur_pos: LatLon, signal_count: int):
        pass

class PathFinder(ABC):
    def __init__(self, res: int, centre: Tuple[float, float]):
        """
        - `res`: H3 Resolution
        - `centre`: Starting position for pathfinder, as tuple of latitude, longitude
        """
        self.res = res
        self.centre_hex = h3.geo_to_h3(centre[0], centre[1], resolution=self.res)

    @abstractmethod
    def find_next_step(self, current_position: Tuple[float, float], prob_map: np.ndarray) -> Tuple[float, float]:
        """
        Find the next step to go to.

        Args:
            current_position (Tuple[float, float]): Current coordinates lat lon
            prob_map: np.ndarray - of size 7*..7 equal to size of dimension
        Returns:
            Tuple[float, float] - Next step coordinates in lat lon.
        """
        pass

class OutwardSpiralPathFinder(PathFinder):
    def __init__(self, res: int, centre: tuple):
        super().__init__(res, centre)
        self.segment_start_ij_coord = None
        self.next_path_segment = []
        self.k_ring = 1

        centre_ij_coord = h3.experimental_h3_to_local_ij(
            self.centre_hex, self.centre_hex)
        self.next_path_segment.append(centre_ij_coord)
        self.segment_start_ij_coord = centre_ij_coord

    # Create path over an entire circle
    def ring_edge_traversal(self, repetitions, current_ij_coord, i_increment, j_increment):
        for i in range(repetitions):
            current_ij_coord = (
                current_ij_coord[0]+i_increment, current_ij_coord[1]+j_increment)
            self.next_path_segment.append(current_ij_coord)
        return current_ij_coord

    # Implementation of abstract method that returns next waypoint
    def find_next_step(self, current_position: Tuple[float, float], prob_map: Dict) -> Tuple[float, float]:
        current_position_ij = h3.experimental_h3_to_local_ij(self.centre_hex, h3.geo_to_h3(
            current_position[0], current_position[1], resolution=self.res))

        # Waypoints are calculated based on ring
        if len(self.next_path_segment) == 1 and self.segment_start_ij_coord == current_position_ij:
            self.segment_start_ij_coord = self.ring_edge_traversal(
                1, self.segment_start_ij_coord, 0, -1)
            self.segment_start_ij_coord = self.ring_edge_traversal(
                self.k_ring-1, self.segment_start_ij_coord, 1, 0)
            self.segment_start_ij_coord = self.ring_edge_traversal(
                self.k_ring, self.segment_start_ij_coord, 1, 1)
            self.segment_start_ij_coord = self.ring_edge_traversal(
                self.k_ring, self.segment_start_ij_coord, 0, 1)
            self.segment_start_ij_coord = self.ring_edge_traversal(
                self.k_ring, self.segment_start_ij_coord, -1, 0)
            self.segment_start_ij_coord = self.ring_edge_traversal(
                self.k_ring, self.segment_start_ij_coord, -1, -1)
            self.segment_start_ij_coord = self.ring_edge_traversal(
                self.k_ring, self.segment_start_ij_coord, 0, -1)
            self.k_ring += 1

        if current_position_ij == self.next_path_segment[0]:
            self.next_path_segment.pop(0)
            return h3.h3_to_geo(h3.experimental_local_ij_to_h3(self.centre_hex, self.next_path_segment[0][0], self.next_path_segment[0][1]))
        else:
            print("Previous waypoint may not be correct")
            return None

class BayesianHexSearch(PathFinder):
    """A pathfinding algorithm in the H3 hexagonal grid system using probability.
    """

    def __init__(self, res: int, center: tuple) -> None:
        """Initializes with given resolution and starting position

        Args:
            res (int): The H3 resolution for the hexagonal grid.
            center (tuple[float, float]): Starting position as a tuple of (latitude, longitude).
        """
        super().__init__(res, center)
        self.trajectory = []

    def find_next_step(self, current_position: tuple[float, float], prob_map: dict) -> tuple[int, int]:
        """Determines the next waypoint based on current position and a probability map.

        Args:
            current_position (tuple[float, float]): Current position as a tuple of (latitude, longitude).
        Returns:
            tuple[int, int]: Next waypoint as a tuple of (latitude, longitude).
        """
        # Initialise current position
        curr_hexagon = h3.geo_to_h3(
            current_position[0], current_position[1], resolution=self.res)

        # Hex index of the highest probability
        max_hex_index = max(prob_map, key=lambda key: prob_map[key])

        # Get neighbours
        neighbours = h3.k_ring(curr_hexagon, 1)

        # Initialise variables to find the nest best neighbour
        path_to_max = h3.h3_line(curr_hexagon, max_hex_index)
        best_neighbour = path_to_max[1]
        highest_score = 0

        for neighbour in neighbours:
            if neighbour not in prob_map:
                continue
            dist = distance_between_2_hexas(neighbour, max_hex_index)
            neighbour_prob = prob_map[neighbour]
            # TODO: Test different parameters for this
            score = 1/(1+dist) * 100 + neighbour_prob * 10
            # score = neighbour_prob * 10

            if score > highest_score:
                best_neighbour = neighbour
                highest_score = score

        return h3.h3_to_geo(best_neighbour)