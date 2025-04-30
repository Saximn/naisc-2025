'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'

// Import MapboxHeatmap dynamically to prevent SSR issues
const MapboxHeatmap = dynamic(() => import('./MapBoxHeatMap'), {
  ssr: false
})

// Define the props interface
interface RiskMapProps {
  incidentType: string
  floodData: Array<{
    lat: number
    lon: number
    val: number
  }>
}

export default function RiskMap({ incidentType, floodData = [] }: RiskMapProps) {
  // Crime and fire data are still generated on demand in this component
  const generateRandomData = (count: number = 400) => {
    return Array.from({ length: count }, () => ({
      lat: 1.2 + Math.random() * 0.4, // Latitude within Singapore range
      lon: 103.6 + Math.random() * 0.5, // Longitude within Singapore range
      val: Math.random(), // Random value between 0 and 1
    }))
  }
  
  // Generate random data for non-flood incident types once
  const [crimeData] = useState(() => generateRandomData())
  const [fireData] = useState(() => generateRandomData())
  
  // Determine which data to display based on incident type
  const getDisplayData = () => {
    switch (incidentType) {
      case 'flood':
        return floodData
      case 'crime':
        return crimeData
      case 'fire':
        return fireData
      default:
        return []
    }
  }
  
  return (
    <div className="h-96 w-full">
      <MapboxHeatmap 
        incidentType={incidentType} 
        customData={getDisplayData()} 
      />
    </div>
  )
}