import { React, useState } from "react";
import {
  MapContainer,
  TileLayer,
  useMapEvents,
  GeoJSON,
  LayersControl,
  FeatureGroup,
  Marker,
  Popup,
  Circle,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { polygonToCells, cellToBoundary } from "h3-js";
import "./Map.css";
import DroneMarker from "./DroneMarker";

import L from "leaflet";
import ReactDOMServer from "react-dom/server";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import PlaceIcon from "@mui/icons-material/Place";
import AccessibilityIcon from "@mui/icons-material/Accessibility";

export default function Map({
  drones,
  hotspots,
  clusters,
  detectedEntities,
  setMap,
}) {
  const start_position = [1.3430293739520736, 103.9591294705276];
  const [hexagons, setHexagons] = useState([]);

  function H3Overlay() {
    const map = useMapEvents({
      dragend: () => updateHexagons(),
      zoomend: () => updateHexagons(),
    });

    const updateHexagons = () => {
      const bounds = map.getBounds();
      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();
      const expansionAmount = 0.005; // Adjust this value as needed

      // Reference: https://github.com/matthiasfeist/what-the-h3index
      const boundingBox = [
        [sw.lng - expansionAmount, sw.lat - expansionAmount], // Expanded SW corner
        [ne.lng + expansionAmount, sw.lat - expansionAmount], // Bottom-right corner
        [ne.lng + expansionAmount, ne.lat + expansionAmount], // Expanded NE corner
        [sw.lng - expansionAmount, ne.lat + expansionAmount], // Top-left corner
        [sw.lng - expansionAmount, sw.lat - expansionAmount], // Closing the loop (back to expanded SW corner)
      ];

      const h3Resolution = calculateH3Resolution(map.getZoom());

      const hexIndexes = polygonToCells(boundingBox, h3Resolution, true);

      const hexFeatures = hexIndexes.map((index) => {
        const boundary = cellToBoundary(index);
        return {
          type: "Feature",
          properties: {},
          geometry: {
            type: "Polygon",
            coordinates: [boundary.map((coord) => [coord[1], coord[0]])],
          },
        };
      });

      setHexagons(hexFeatures);
    };

    const calculateH3Resolution = (zoom) => {
      // Implement logic to determine resolution based on zoom level
      return 11; // Placeholder value
    };

    return null;
  }

  const createHotSpotIcon = () => {
    const iconHtml = ReactDOMServer.renderToString(
      <WhatshotIcon style={{ color: "red", sx: 200 }} />
    );
    return L.divIcon({
      html: iconHtml,
      className: "custom-leaflet-icon", // Adjust as needed, ensure this class does minimal or no styling to avoid conflicts
      iconSize: L.point(30, 30), // Adjust size as needed
      iconAnchor: L.point(15, 30), // Adjust anchor as needed, consider the icon size
    });
  };

  const createDetectionIcon = () => {
    const iconHtml = ReactDOMServer.renderToString(
      <AccessibilityIcon style={{ color: "bright orange", sx: 200 }} />
    );
    return L.divIcon({
      html: iconHtml,
      className: "custom-leaflet-icon", // Adjust as needed, ensure this class does minimal or no styling to avoid conflicts
      iconSize: L.point(30, 30), // Adjust size as needed
      iconAnchor: L.point(15, 30), // Adjust anchor as needed, consider the icon size
    });
  };

  const addHotspot = (latlng) => {
    const url = "http://127.0.0.1:5000/hotspot/add";
    const params = new URLSearchParams();
    params.append("hotspot_position", JSON.stringify({ latlng }));
    fetch(url, { method: "POST", body: params });
  };

  const createClusterIcon = () => {
    const iconHtml = ReactDOMServer.renderToString(
      <PlaceIcon style={{ color: "blue", sx: 200 }} />
    );
    return L.divIcon({
      html: iconHtml,
      className: "custom-leaflet-cluster-icon", // Adjust as needed, ensure this class does minimal or no styling to avoid conflicts
      iconSize: L.point(30, 30), // Adjust size as needed
      iconAnchor: L.point(15, 30), // Adjust anchor as needed, consider the icon size
    });
  };
  const createNumberIcon = (number) => {
    const iconHtml = `<div style="background-color: white; color: black; border-radius: 50%; width: 30px; height: 30px; display: flex; justify-content: center; align-items: center; font-size: 12px; border: 1px solid black;">${number}</div>`;
    return L.divIcon({
      html: iconHtml,
      className: "my-custom-icon", // Ensure this class does minimal or no styling to avoid conflicts
      iconSize: [30, 30], // Adjust size as needed
      iconAnchor: [15, 30], // Adjust anchor as needed, consider the icon size
    });
  };
  function getNewPosition(lat, lon, distanceInMeters) {
    const EarthRadius = 6378137;
    const dLat = distanceInMeters / EarthRadius;
    const dLatDegrees = dLat * (180 / Math.PI);

    return {
      lat: lat + dLatDegrees,
      lon: lon,
    };
  }

  return (
    <>
      <MapContainer
        center={start_position}
        zoom={18}
        minZoom={16}
        maxZoom={30}
        scrollWheelZoom={true}
        ref={setMap}>
        <TileLayer
          zoom={18}
          maxZoom={30}
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <AddHotspotOnClick onNewPoint={addHotspot} />
        <LayersControl>
          <LayersControl.Overlay name="H3 Overlay">
            <FeatureGroup>
              <H3Overlay />
              <GeoJSON
                key={hexagons.length}
                data={{ type: "FeatureCollection", features: hexagons }}
              />
            </FeatureGroup>
          </LayersControl.Overlay>
        </LayersControl>
        {drones
          .filter(
            (drone) => drone.position.lat != null && drone.position.lon != null
          )
          .map((drone) => (
            <DroneMarker
              key={drone.drone_id}
              drone_id={drone.drone_id}
              battery_percentage={drone.battery_percentage}
              lon={drone.position.lon}
              lat={drone.position.lat}
              mode={drone.mode}></DroneMarker>
          ))}
        {detectedEntities.map((entity, index) => (
          <Marker
            key={index}
            position={{
              lat: entity.coordinates.lat,
              lng: entity.coordinates.lon,
            }}
            icon={createDetectionIcon()}></Marker>
        ))}
        {hotspots.map((hotspot, index) => (
          <Marker
            key={index}
            position={{ lat: hotspot[0], lng: hotspot[1] }}
            icon={createHotSpotIcon()}>
            <Popup>{`Latitude: ${hotspot[0]}, Longitude: ${hotspot[1]}`}</Popup>
          </Marker>
        ))}
        {clusters.map((cluster, index) => (
          <div key={`marker-${index}`}>
            <Marker
              key={`marker-${index}`}
              position={{ lat: cluster[0][0], lng: cluster[0][1] }}
              icon={createClusterIcon()}>
              <Popup>
                {`Latitude: ${cluster[0]}, Longitude: ${cluster[0]}`}
              </Popup>
            </Marker>
            <Circle
              key={`circle-${index}`}
              center={{ lat: cluster[0][0], lng: cluster[0][1] }}
              radius={cluster[1]}
              color="blue"
              fillColor="blue"
              fillOpacity={0.2}
            />
            <Marker
              key={`number-${index}`}
              position={getNewPosition(cluster[0][0], cluster[0][1], 20)}
              icon={createNumberIcon(index + 1)}
              zIndexOffset={1000}
            />
          </div>
        ))}
      </MapContainer>
    </>
  );

  function AddHotspotOnClick({ onNewPoint }) {
    useMapEvents({
      click(e) {
        onNewPoint(e.latlng);
      },
    });
    return null;
  }
}
