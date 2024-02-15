import React, { useState, useEffect, useRef } from "react";
import Tab from "./Tab.js";
import Sidebar from "./Sidebar.js";
import DroneStatusCard from "./DroneStatusCard.js";

import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import KeyboardArrowLeftIcon from "@mui/icons-material/KeyboardArrowLeft";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";

import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Divider from "@mui/material/Divider";

export default function SidebarComponent({ map, drones, hotspots }) {
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
    console.log(url, params);
    fetch(url, { method: "POST", body: params });
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
          id="hotspots"
          header="Hotspots"
          icon={<FormatListBulletedIcon />}
          active>
          <Box sx={{ padding: 2 }}>
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
          </Box>
        </Tab>
      </Sidebar>
    </>
  );
}
