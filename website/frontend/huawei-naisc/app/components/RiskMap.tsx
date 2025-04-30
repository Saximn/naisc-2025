'use client'

import { SetStateAction, useEffect, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import dynamic from 'next/dynamic'

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
interface RiskMapProps {
  incidentType: string
}

const MapboxHeatmap = dynamic(() => import('./MapBoxHeatMap'), { ssr: false })

export default function RiskMap({ incidentType }: RiskMapProps) {
  return (
    <div className="map-container">
      <MapboxHeatmap incidentType={incidentType} />
    </div>
  )
}
