import threading
import logging
from queue import Queue, Empty
from typing import Dict, Tuple

from maplib import LatLon
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
        self.drone_sys = DroneSystem(drone_states, HOME_POSITION, detected_queue)
        self.drone_states = drone_states

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

def main(args=None):
    mission = Mission()
    drone_states = {
        DroneId(69): DroneState(69),
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
    drone_sys = DroneSystem(drone_states, HOME_POSITION, detected_queue=detected_queue)
    drone_sys.start()
    drone_sys.connect_drones()

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