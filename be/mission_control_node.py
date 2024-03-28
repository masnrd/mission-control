from datetime import datetime
import random
import threading
import logging
from queue import Queue, Empty
from typing import Dict, Tuple

from drone_utils import DroneId, DroneState, DroneCommand, DroneCommandId
from detection_utils import DetectedEntity
from mission_control_webserver import MCWebServer
from fake_drone_system import DroneSystem
from mission_utils import Mission
from constants import HOME_POSITION

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

COMMAND_CHECK_INTERVAL = 1
class MCNode:
    def __init__(self, drone_states: Dict[DroneId, DroneState], commands: Queue[Tuple[DroneId, DroneCommand]], detected_queue: Queue[DetectedEntity]):
        self.logger = logging.getLogger("mission_control")
        self.drone_sys = DroneSystem(drone_states, HOME_POSITION)
        self.drone_states = drone_states
        self.detected_queue:Queue[DetectedEntity] = detected_queue

        # Initialise command queue
        self.command_loop = threading.Timer(COMMAND_CHECK_INTERVAL, self.check_command_loop)
        self.commands: Queue[Tuple[DroneId, DroneCommand]] = commands
        self.logger.info("Mission Control initialised.")

    def start_node(self):
        self.command_loop.start()

    def log(self, msg: str):
        self.logger.info(f"MISSION CONTROL: {msg}")

    def raise_error(self, msg: str):
        self.logger.error(f"MISSION CONTROL ERROR: {msg}")
        raise Exception(msg)
    
    def check_command_loop(self):
        """ Loop to check for commands from the webserver """
        try:
            self.random_detection()
            drone_id, command = self.commands.get(block=False)
            print(f"MISSION CONTROL: User entered command {DroneCommandId(command.command_id).name}")
            if drone_id not in self.drone_states.keys():
                print(f"Warning: No such drone ID {drone_id}")
                return
            self.mc_send_command(drone_id, command)
        except Empty:
            pass
        self.command_loop = threading.Timer(COMMAND_CHECK_INTERVAL, self.check_command_loop)
        self.command_loop.start()

    def mc_send_command(self, drone_id: DroneId, drone_cmd: DroneCommand):
        """ MC sends a Command to a given drone """
        self.drone_sys.add_command(drone_id, drone_cmd)

    def random_detection(self):
        DICSOVERY_PROBABILITY = 0.5
        guess = random.random()
        drone_ids = list(self.drone_states.keys())
        if guess < DICSOVERY_PROBABILITY:
            drone_id = random.choice(drone_ids)
            self.detected_queue.put(DetectedEntity(drone_id=drone_id, coordinates=self.drone_states[drone_id].get_position(), time_found=datetime.now()))

def main(args=None):
    mission = Mission()
    drone_states = {
        DroneId(1): DroneState(1),
        DroneId(2): DroneState(2),
        DroneId(3): DroneState(3),
        DroneId(4): DroneState(4),
    }
    commands: Queue[Tuple[DroneId, DroneCommand]] = Queue()
    detected_queue: Queue[DetectedEntity] = Queue()

    # Start web server
    webserver = MCWebServer(mission, drone_states, commands, detected_queue)
    webserver_thread = threading.Thread(target=webserver.run, daemon=True)
    webserver_thread.start()

    # Start rclpy node
    mcnode = MCNode(drone_states, commands, detected_queue)
    mcnode.start_node()

    # Start drones
    drone_sys = DroneSystem(drone_states, HOME_POSITION)
    drone_sys.start()
    drone_sys.connect_drones()

    #TODO:
    # mission.hotspots.add((1.3401246069622084, 103.96241597604688))
    # mission.hotspots.add((1.3402533177739138, 103.96256617975436))
    # from run_clustering import run_clustering
    # print(f'Hotspots:{mission.hotspots}')

    # cluster_centres = run_clustering(mission.hotspots) # cluster_centres: Dict[int, Tuple[Tuple[float,float], List[Tuple[float,float]]]]
    # print(f'Clusters:{cluster_centres}')
    # # Each cluster center value is represented by a tuple: (centre latlon, list of latlon hotspots)
    # mission.cluster_centres = cluster_centres
    # mission.cluster_centres_to_explore = [cluster for cluster in cluster_centres.values()]

    # assignments = mcnode.assigner.fit(mission.cluster_centres_to_explore, drone_states)
    # for drone_id, cluster in assignments.items():
    #     hotspots_in_cluster = cluster
    #     print(f'Cluster center:{cluster[0][0], cluster[0][1]}, hotspots: {cluster[1]}')
    #     command_tup = (drone_id, DroneCommand_SEARCH_SECTOR(LatLon(cluster[0][0], cluster[0][1]), cluster[1]))
    #     self.commands.put_nowait(command_tup)

    # import folium
    # m = folium.Map()
    # from pathfinder.viz import visualise_hex_dict_to_map
    # visualise_hex_dict_to_map()

    try:
        while True:
            user_in = input() # nth done here, just to avoid busy waiting
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    finally:
        drone_sys.exit.set()


if __name__ == '__main__':
    main()