"use client";

import dynamic from "next/dynamic";

interface Point {
  lat: number;
  lon: number;
  label: string;
}

const MapInner = dynamic(() => import("./map-inner"), { ssr: false });

export function ArrestMap({ points }: { points: Point[] }) {
  return <MapInner points={points} />;
}
