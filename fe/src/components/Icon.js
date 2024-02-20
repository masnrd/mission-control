import React from "react";
import markerIconPng from "leaflet/dist/images/marker-icon.png";
import L from "leaflet";
import { Marker } from "react-leaflet";
import ReactDOMServer from "react-dom/server";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import AccessibilityIcon from "@mui/icons-material/Accessibility";
import PlaceIcon from "@mui/icons-material/Place";

function createDroneIcon(props) {
  const droneIcon = L.icon({
    iconUrl: markerIconPng,
  });
  return (
    <>
      <Marker
        key={props.drone_id}
        position={[props.lat, props.lon]}
        icon={droneIcon}></Marker>
    </>
  );
}

const createHotSpotIcon = () => {
    const iconHtml = ReactDOMServer.renderToString(
      <WhatshotIcon style={{ color: "red", sx: 200 }} />
    );
    return L.divIcon({
      html: iconHtml,
      className: "custom-leaflet-icon",
      iconSize: L.point(30, 30),
      iconAnchor: L.point(15, 30),
    });
  };

  const createDetectionIcon = () => {
    const iconHtml = ReactDOMServer.renderToString(
      <AccessibilityIcon style={{ color: "bright orange", sx: 200 }} />
    );
    return L.divIcon({
      html: iconHtml,
      className: "custom-leaflet-icon",
      iconSize: L.point(30, 30),
      iconAnchor: L.point(15, 30),
    });
  };

  const createClusterIcon = () => {
    const iconHtml = ReactDOMServer.renderToString(
      <PlaceIcon style={{ color: "blue", sx: 200 }} />
    );
    return L.divIcon({
      html: iconHtml,
      className: "custom-leaflet-cluster-icon",
      iconSize: L.point(30, 30),
      iconAnchor: L.point(15, 30),
    });
  };
  const createNumberIcon = (number) => {
    const iconHtml = `<div style="background-color: white; color: black; border-radius: 50%; width: 30px; height: 30px; display: flex; justify-content: center; align-items: center; font-size: 12px; border: 1px solid black;">${number}</div>`;
    return L.divIcon({
      html: iconHtml,
      className: "my-custom-icon",
      iconSize: [30, 30],
      iconAnchor: [15, 30],
    });
  };

export default {
  createDroneIcon,
  createHotSpotIcon,
  createDetectionIcon,
  createClusterIcon,
  createNumberIcon,
};
