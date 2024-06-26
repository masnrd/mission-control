"""
mission_control_webserver:
A Flask webserver that:
- Provides a REST API to interact with drones.
    - When a route is called, the route function generates the necessary command with the `DroneCommand` API,
    and places it in the command queue in `self.commands`. This command queue is accessed every second (by default).
    - Drone information is obtained by accessing the getters or `toJSON()` methods of the drone states
- Provides a web client to interact with the API.
    - The web client is provided in the `static` directory provided in the package.
"""
import logging
import json
from flask import Flask, jsonify, request, send_from_directory, Response
from typing import Dict, Tuple
from queue import Queue
from pathlib import Path
from assigner.simplequeueassigner import SimpleQueueAssigner
from detection_utils import DetectedEntity

from mission_utils import Mission, SetEncoder
from drone_utils import DroneState, DroneId, PathAlgo
from drone_utils import DroneCommand, DroneCommand_SEARCH_SECTOR, DroneCommand_MOVE_TO
from run_clustering import run_clustering
from maplib import LatLon
from flask_cors import CORS

logging.getLogger("flask_cors").level = logging.ERROR
logging.getLogger("werkzeug").level = logging.ERROR

class MCWebServer:
    def __init__(self, mission:Mission, drone_states: Dict[int, DroneState], commands: Queue[Tuple[DroneId, DroneCommand]], detected_queue: Queue[DetectedEntity]):
        self.static_dir = Path("frontend")
        # Flask.logger_name = "listlogger"
        app = Flask(
            "Mission Control", 
            static_url_path='',
            static_folder=self.static_dir,
            template_folder=self.static_dir,
        )
        cors = CORS(app, resources={r"/*": {"origins": "*"}})
        self.app = app

        self.mission = mission
        self.drone_states = drone_states
        self.commands: Queue[Tuple[DroneId, DroneCommand]] = commands
        self.assigner = SimpleQueueAssigner()
        self.detected_queue = detected_queue

        # Set up Endpoints
        self.app.add_url_rule("/", view_func=self.route_index)
        self.app.add_url_rule("/api/info", view_func=self.route_info)
        self.app.add_url_rule("/hotspot/add", methods=["POST"], view_func=self.route_add_hotspot)
        self.app.add_url_rule("/hotspot/delete", methods=["POST"], view_func=self.route_delete_hotspot)
        self.app.add_url_rule("/api/action/moveto", view_func=self.route_action_moveto)
        self.app.add_url_rule("/api/action/rtb", view_func=self.route_action_rtb)
        self.app.add_url_rule("/api/action/land", view_func=self.route_action_land)
        self.app.add_url_rule("/api/action/disconnect", view_func=self.route_action_disconnect)
        self.app.add_url_rule("/api/setup/run_clustering", view_func=self.route_run_clustering)
        self.app.add_url_rule("/api/setup/start_operation", view_func=self.route_start_operation)
        self.app.after_request(self.add_headers)

    def route_index(self):
        return send_from_directory(self.static_dir, "index.html")

    def route_info(self) -> Dict:
        drones = {}
        for drone_id, drone_state in self.drone_states.items():
            drones[drone_id] = drone_state.toJSON()  # Ensure this method returns a serializable dictionary

        while not self.detected_queue.empty():
            self.mission.detected.append(self.detected_queue.get())

        ret = {
            "drones": drones,
            "hotspots": self.mission.hotspots,  # Assuming this is already serializable
            "clusters": self.mission.cluster_centres,  # Assuming this is already serializable
            "clusters_to_explore" : self.mission.cluster_centres_to_explore,
            "detected" : [entity.to_dict() for entity in self.mission.detected]
        }
        
        return jsonify(ret)
    
    def route_action_moveto(self) -> Tuple[Dict, int]:
        drone_id = request.args.get("drone_id", type=int, default=None)
        lat = request.args.get("lat", type=float, default=None)
        lon = request.args.get("lon", type=float, default=None)

        if drone_id is None:
            return {"error": "need drone_id"}, 400

        if lat is None or lon is None:
            return {"error": "need latitude/longitude parameters as float"}, 400
        
        # Place command in command queue
        command_tup = (drone_id, DroneCommand_MOVE_TO(LatLon(lat, lon)))
        self.commands.put_nowait(command_tup)
        
        return {}, 200
    
        
        return {}, 200
    
    def route_action_rtb(self) -> Tuple[Dict, int]:
        drone_id = request.args.get("drone_id", type=int, default=None)
        lat = request.args.get("lat", type=float, default=None)
        lon = request.args.get("lon", type=float, default=None)

        if drone_id is None:
            return {"error": "need drone_id"}, 400

        if lat is None or lon is None:
            return {"error": "need latitude/longitude parameters as float"}, 400
        
        # Place command in command queue
        print(f'command_tup = ({drone_id}, DroneCommand_RTB(LatLon({lat}, {lon}), None))')
        
        return {}, 200
    
    def route_action_land(self) -> Tuple[Dict, int]:
        drone_id = request.args.get("drone_id", type=int, default=None)

        if drone_id is None:
            return {"error": "need drone_id"}, 400
        
        # Place command in command queue
        print(f'command_tup = ({drone_id}, DroneCommand_LAND())')
        
        return {}, 200
    
    def route_action_disconnect(self) -> Tuple[Dict, int]:
        drone_id = request.args.get("drone_id", type=int, default=None)

        if drone_id is None:
            return {"error": "need drone_id"}, 400
        
        # Place command in command queue
        print(f'command_tup = ({drone_id}, DroneCommand_DISCONNECT())')
        
        return {}, 200
    
    def route_add_hotspot(self):
        data = request.form.to_dict()
        hotspot = json.loads(data.get('hotspot_position', None))
        if (hotspot["latlng"]["lat"],hotspot["latlng"]["lng"]) not in self.mission.hotspots:
            self.mission.hotspots.append((hotspot["latlng"]["lat"],hotspot["latlng"]["lng"])) # Should be a set here
        else:
            print("Already added")
        return {}, 200
    
    def route_delete_hotspot(self):
        data = request.form.to_dict()
        hotspot = json.loads(data.get('hotspot_position', None))
        self.mission.hotspots.remove((hotspot["latlng"][0],hotspot["latlng"][1])) # Should be a set here
        return {}, 200

    def route_run_clustering(self):
        cluster_centres = run_clustering(self.mission.hotspots) # cluster_centres: Dict[int, Tuple[Tuple[float,float], List[Tuple[float,float]]]]
        # Each cluster center value is represented by a tuple: (centre latlon, list of latlon hotspots)
        self.mission.cluster_centres = cluster_centres
        self.mission.cluster_centres_to_explore = [cluster for cluster in cluster_centres.values()]
        return cluster_centres
    
    def route_start_operation(self):
        """Run assignment on drones in drone state, cluster centers and command drones to search sector"""
        algo = request.args.get("path_algo", type=str, default="bayes")
        assignments = self.assigner.fit(self.mission.cluster_centres_to_explore, self.drone_states)
        for drone_id, cluster in assignments.items():
            if algo == "bayes": command_tup = (drone_id, DroneCommand_SEARCH_SECTOR(LatLon(cluster[0][0], cluster[0][1]), cluster[1], PathAlgo.BAYES))
            else: command_tup = (drone_id, DroneCommand_SEARCH_SECTOR(LatLon(cluster[0][0], cluster[0][1]), cluster[1], PathAlgo.SPIRAL))
            self.commands.put_nowait(command_tup)
        return {}, 200        

    def add_headers(self, response: Response):
        response.headers.add("Content-Type", "application/json")
        response.headers.add("Access-Control-Allow-Methods", "PUT, GET ,POST, DELETE, OPTIONS")
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.status = 200
        return response
    
    def run(self):
        self.app.run(debug=True, use_reloader=False)