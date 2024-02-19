

import datetime
from typing import Dict

from maplib import LatLon


class DetectedEntity:
    """
    Detected object
    """
    def __init__(self, drone_id:int, coordinates:LatLon, time_found: datetime.datetime):
        self.drone_id = drone_id
        self.coordinates = coordinates
        self.time_found = time_found

    def to_dict(self) -> Dict:
        """
        Serialize the DetectedEntity to a dictionary.
        """
        return {
            "drone_id": self.drone_id,
            "coordinates": self.coordinates.__dict__,  # Modify this according to how LatLon is implemented
            "time_found": self.time_found.isoformat()  # Convert datetime to ISO 8601 string
        }