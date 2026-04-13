"use client";

import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { withBasePath } from "@/lib/base-path";

interface Point {
  lat: number;
  lon: number;
  label: string;
}

// Fix default marker icon issue with Next.js/webpack
const icon = new L.Icon({
  iconUrl: withBasePath("/leaflet/marker-icon.png"),
  iconRetinaUrl: withBasePath("/leaflet/marker-icon-2x.png"),
  shadowUrl: withBasePath("/leaflet/marker-shadow.png"),
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

export default function MapInner({ points }: { points: Point[] }) {
  if (points.length === 0) return null;

  const center: [number, number] = [
    points.reduce((s, p) => s + p.lat, 0) / points.length,
    points.reduce((s, p) => s + p.lon, 0) / points.length,
  ];

  return (
    <MapContainer
      center={center}
      zoom={12}
      style={{ height: "350px", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {points.map((p, i) => (
        <Marker key={i} position={[p.lat, p.lon]} icon={icon}>
          <Popup>{p.label}</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
