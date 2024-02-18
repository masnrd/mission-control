import React, { useState } from "react";
import Tab from "./Tab.js";
import Sidebar from "./Sidebar.js";
import DroneStatusCard from "./DroneStatusCard.js";

import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import KeyboardArrowLeftIcon from "@mui/icons-material/KeyboardArrowLeft";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";
import AddLocationIcon from "@mui/icons-material/AddLocation";
import GpsFixedIcon from "@mui/icons-material/GpsFixed";

import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Divider from "@mui/material/Divider";
import Button from "@mui/material/Button";

export default function SidebarComponent({ map, drones, hotspots, clusters }) {
  const [openTab, setOpenTab] = useState("home");
  const onClose = () => {
    setOpenTab(false);
  };

  const onOpen = (id) => {
    setOpenTab(id);
  };
  const removeHotspot = (latlng) => {
    const url = "http://127.0.0.1:5000/hotspot/delete";
    const params = new URLSearchParams();
    params.append("hotspot_position", JSON.stringify({ latlng }));
    fetch(url, { method: "POST", body: params });
  };
  function runClustering() {
    try {
      const response = fetch("http://127.0.0.1:5000/api/setup/run_clustering");
      if (response.ok) {
        console.log("Run clustering:", response.json());
      } else {
        console.error("Error:", response.status, response.statusText);
      }
    } catch (error) {
      console.error("Error:", error);
    }
  }
  const assignForSearch = () => {
    try {
      const response = fetch("http://127.0.0.1:5000/api/setup/start_operation");
      if (response.ok) {
        console.log("Assign for search:", response.json());
      } else {
        console.error("Error:", response.status, response.statusText);
      }
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <>
      <Sidebar
        map={map}
        position="left"
        collapsed={!openTab}
        selected={openTab}
        closeIcon={<KeyboardArrowLeftIcon />}
        onClose={onClose}
        onOpen={onOpen}
        panMapOnChange
        rehomeControls>
        <Tab id="home" header="Drones" icon={<FormatListBulletedIcon />} active>
          {drones.map((drone) => (
            <DroneStatusCard key={drone.drone_id} droneData={drone} map={map} />
          ))}
        </Tab>
        <Tab
          id="clustering"
          header="Clustering"
          icon={<FormatListBulletedIcon />}
          active>
          <Box sx={{ padding: 2 }}>
            <h1>Hotspot</h1>
            {hotspots.map((hotspot, index) => (
              <React.Fragment key={index}>
                <Box
                  sx={{
                    marginBottom: 2,
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                  }}>
                  <AddIcon color="primary" />
                  <Typography>
                    Latitude: {hotspot[0]} Longitude: {hotspot[1]}
                  </Typography>
                  <IconButton
                    aria-label="delete"
                    onClick={() => removeHotspot(hotspot)}>
                    <DeleteIcon />
                  </IconButton>
                </Box>
                {index < hotspots.length - 1 && <Divider />}
              </React.Fragment>
            ))}
            <h1>Clusters</h1>
            {clusters.map((cluster, index) => (
              <div key={`marker-${index}`}>
                <Box
                  sx={{
                    marginBottom: 2,
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                  }}>
                  <AddLocationIcon color="primary" />
                  <Typography>
                    Lat: {cluster[0][0].toFixed(5)} Lon:{" "}
                    {cluster[0][1].toFixed(5)}
                  </Typography>
                </Box>
                {index < hotspots.length - 1 && <Divider />}
              </div>
            ))}
          </Box>
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 2 }}>
            <Button
              variant="outlined"
              color="primary"
              onClick={runClustering}
              startIcon={<GpsFixedIcon />}>
              Run Clustering
            </Button>
          </Box>
          <Box sx={{ display: "flex", justifyContent: "center", marginTop: 2 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={assignForSearch}
              startIcon={<GpsFixedIcon />}>
              Assign and Search
            </Button>
          </Box>
        </Tab>
      </Sidebar>
    </>
  );
}
