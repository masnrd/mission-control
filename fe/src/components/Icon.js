import React from "react";
import L from "leaflet";
import ReactDOMServer from "react-dom/server";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import AccessibilityIcon from "@mui/icons-material/Accessibility";
import PlaceIcon from "@mui/icons-material/Place";
import DroneIconUrl from "../assets/drone.svg"

const createDroneIcon = (number) => {
  const iconHtml = `
    <div style="position: relative; width: 50px; height: 50px;">
      <img src="${DroneIconUrl}" style="width: 100%; height: 100%;" />
      <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; font-size: 14px; color: white;">
        ${number}
      </div>
    </div>
  `;

  return L.divIcon({
    html: iconHtml,
    iconSize: [50, 50],
    iconAnchor: [25, 25],
    className: ''
  });
};

const createHotSpotIcon = () => {
  const iconHtml = ReactDOMServer.renderToString(
    <WhatshotIcon style={{color: "red", sx: 200}}/>
  );
  return L.divIcon({
    html: iconHtml,
    className: "custom-leaflet-icon",
    iconSize: L.point(30, 30),
    iconAnchor: L.point(15, 15),
  });
};

const createDetectionIcon = () => {
  const iconHtml = ReactDOMServer.renderToString(
    <AccessibilityIcon style={{color: "bright orange", sx: 200}}/>
  );
  return L.divIcon({
    html: iconHtml,
    className: "custom-leaflet-icon",
    iconSize: L.point(30, 30),
    iconAnchor: L.point(15, 15),
  });
};

const createClusterIcon = () => {
  const iconHtml = ReactDOMServer.renderToString(
    <PlaceIcon style={{color: "blue", sx: 200}}/>
  );
  return L.divIcon({
    html: iconHtml,
    className: "custom-leaflet-cluster-icon",
    iconSize: L.point(30, 30),
    iconAnchor: [15, 15],
  });
};
const createNumberIcon = (number) => {
  const iconHtml = `<div style="background-color: white; color: black; border-radius: 50%; width: 30px; height: 30px; display: flex; justify-content: center; align-items: center; font-size: 12px; border: 1px solid black;">${number}</div>`;
  return L.divIcon({
    html: iconHtml,
    className: "my-custom-icon",
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
};

export default {
  createDroneIcon,
  createHotSpotIcon,
  createDetectionIcon,
  createClusterIcon,
  createNumberIcon,
};
