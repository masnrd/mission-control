import {React, useState} from "react";
import {
  MapContainer,
  TileLayer,
  useMapEvents,
  Marker,
  Popup,
  Circle,
  // LayersControl, FeatureGroup, GeoJSON,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
// import {polygonToCells, cellToBoundary} from "h3-js";
import "./Map.css";
import Icons from "./Icon";
import FakeDetection from "./FakeDetection";


export default function Map({
                              drones,
                              hotspots,
                              clusters,
                              detectedEntities,
                              setMap,
                            }) {
  const start_position = [1.3399775009363866, 103.96258672159254];
  // const [hexagons, setHexagons] = useState([]);
  // function H3Overlay() {
  //   const map = useMapEvents({
  //     dragend: () => updateHexagons(),
  //     zoomend: () => updateHexagons(),
  //   });
  //
  //   const updateHexagons = () => {
  //     const bounds = map.getBounds();
  //     const sw = bounds.getSouthWest();
  //     const ne = bounds.getNorthEast();
  //     // const expansionAmount = 0.005; // Adjust this value as needed
  //     const expansionAmount = 0;
  //
  //     // Reference: https://github.com/matthiasfeist/what-the-h3index
  //     const boundingBox = [
  //       [sw.lng - expansionAmount, sw.lat - expansionAmount], // Expanded SW corner
  //       [ne.lng + expansionAmount, sw.lat - expansionAmount], // Bottom-right corner
  //       [ne.lng + expansionAmount, ne.lat + expansionAmount], // Expanded NE corner
  //       [sw.lng - expansionAmount, ne.lat + expansionAmount], // Top-left corner
  //       [sw.lng - expansionAmount, sw.lat - expansionAmount], // Closing the loop (back to expanded SW corner)
  //     ];
  //
  //     const h3Resolution = calculateH3Resolution(map.getZoom());
  //
  //     const hexIndexes = polygonToCells(boundingBox, h3Resolution, true);
  //
  //     const hexFeatures = hexIndexes.map((index) => {
  //       const boundary = cellToBoundary(index);
  //       return {
  //         type: "Feature",
  //         properties: {},
  //         geometry: {
  //           type: "Polygon",
  //           coordinates: [boundary.map((coord) => [coord[1], coord[0]])],
  //         },
  //       };
  //     });
  //
  //     setHexagons(hexFeatures);
  //   };
  //
  //   const calculateH3Resolution = (zoom) => {
  //     // Implement logic to determine resolution based on zoom level
  //     return 14; // Placeholder value
  //   };
  //
  //   return null;
  // }

  const addHotspot = (latlng) => {
    const url = "http://127.0.0.1:5000/hotspot/add";
    const params = new URLSearchParams();
    params.append("hotspot_position", JSON.stringify({latlng}));
    fetch(url, {method: "POST", body: params});
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
        <AddHotspotOnClick onNewPoint={addHotspot}/>
        {/*<LayersControl>*/}
        {/*  <LayersControl.Overlay name="H3 Overlay">*/}
        {/*    <FeatureGroup>*/}
        {/*      <H3Overlay/>*/}
        {/*      <GeoJSON*/}
        {/*        key={hexagons.length}*/}
        {/*        data={{type: "FeatureCollection", features: hexagons}}*/}
        {/*      />*/}
        {/*    </FeatureGroup>*/}
        {/*  </LayersControl.Overlay>*/}
        {/*</LayersControl>*/}
        {drones
          .filter(drone => drone.position.lat != null && drone.position.lon != null)
          .map(drone => (
            <Marker
              key={drone.drone_id}
              position={{lat: drone.position.lat, lng: drone.position.lon}}
              icon={Icons.createDroneIcon(drone.drone_id)}>
              <Popup>
                Drone ID: {drone.drone_id}<br/>
                Battery: {drone.battery_percentage.toFixed(1)}%<br/>
                Mode: {drone.mode}
              </Popup>
            </Marker>
          ))
        }
        {hotspots.map((hotspot, index) => (
          <Marker
            key={index}
            position={{lat: hotspot[0], lng: hotspot[1]}}
            icon={Icons.createHotSpotIcon()}>
            <Popup>{`(${hotspot[0]}, ${hotspot[1]})`}</Popup>
          </Marker>
        ))}
        {clusters.map((cluster, index) => (
          <div key={`marker-${index}`}>
            <Marker
              key={`marker-${index}`}
              position={{lat: cluster[0][0], lng: cluster[0][1]}}
              icon={Icons.createClusterIcon()}>
              <Popup>
                {`(${cluster[0]}, ${cluster[0]})`}
              </Popup>
            </Marker>
            <Circle
              key={`circle-${index}`}
              center={{lat: cluster[0][0], lng: cluster[0][1]}}
              radius={60}
              color="blue"
              fillColor="blue"
              fillOpacity={0.2}
            />
            <Marker
              key={`number-${index}`}
              position={getNewPosition(cluster[0][0], cluster[0][1], 20)}
              icon={Icons.createNumberIcon(index + 1)}
              zIndexOffset={1000}
            />
          </div>
        ))}
        {detectedEntities.filter(entity => FakeDetection.shouldDisplayEntity(entity, clusters, 0.3)).map((entity, index) => (
          <Marker
            key={`entity-marker-${index}`}
            position={{
              lat: entity.coordinates.lat,
              lng: entity.coordinates.lon,
            }}
            icon={Icons.createDetectionIcon()}
          ></Marker>
        ))}
      </MapContainer>
    </>
  );

  function AddHotspotOnClick({onNewPoint}) {
    useMapEvents({
      click(e) {
        onNewPoint(e.latlng);
      },
    });
    return null;
  }
}
