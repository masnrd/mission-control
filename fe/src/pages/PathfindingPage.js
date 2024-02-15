import { useState, useEffect } from "react";
import Map from "../components/Map";
import SidebarComponent from "../components/SidebarComponent";

export default function Pathfinding() {
  const [map, setMap] = useState(null);
  const [drones, setDrones] = useState([]);
  const [hotspots, setHotspots] = useState([]);

  const url = "http://127.0.0.1:5000/api/info";
  useEffect(() => {
    fetch(url, { mode: "cors" })
      .then((response) => response.json())
      .then((data) => {
        const parsedDrones = Object.values(data["drones"]);
        setDrones(parsedDrones);
        const parsedHotspots = Object.values(data["hotspots"]);
        setHotspots(parsedHotspots);
      })
      .catch((error) => console.error("Error in fetching drone data:", error));
  });

  return (
    <>
      {map && (
        <SidebarComponent map={map} drones={drones} hotspots={hotspots} />
      )}
      <Map drones={drones} hotspots={hotspots} setMap={setMap} />
    </>
  );
}
