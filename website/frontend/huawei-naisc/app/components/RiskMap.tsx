'use client'

import { SetStateAction, useEffect, useState } from 'react'
import { MapContainer, TileLayer, Rectangle, Tooltip, Popup, GeoJSON } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import axios from 'axios'

interface RiskMapProps {
  incidentType: string
}

// This would come from the API in a real app
const dummyRiskData = {
  crime: [
    { id: 1, bounds: [[1.28, 103.84], [1.29, 103.85]], risk: 'high', details: '87% confidence - Recent incidents, unusual social media activity' },
    { id: 2, bounds: [[1.30, 103.82], [1.31, 103.83]], risk: 'medium', details: '65% confidence - Temporal pattern detected' },
    { id: 3, bounds: [[1.33, 103.86], [1.34, 103.87]], risk: 'low', details: '32% confidence - Historical pattern only' },
  ],
  fire: [
    { id: 4, bounds: [[1.32, 103.85], [1.33, 103.86]], risk: 'high', details: '92% confidence - Elevated temperatures, low humidity' },
    { id: 5, bounds: [[1.29, 103.87], [1.30, 103.88]], risk: 'medium', details: '58% confidence - Sensor anomalies detected' },
    { id: 6, bounds: [[1.31, 103.89], [1.32, 103.90]], risk: 'low', details: '29% confidence - Historical risk zone' },
  ],
  flood: [
    { id: 7, bounds: [[1.27, 103.83], [1.28, 103.84]], risk: 'high', details: '88% confidence - Rising water levels, heavy rainfall forecast' },
    { id: 8, bounds: [[1.34, 103.82], [1.35, 103.83]], risk: 'medium', details: '62% confidence - Drainage concerns, moderate rain' },
    { id: 9, bounds: [[1.30, 103.85], [1.31, 103.86]], risk: 'low', details: '35% confidence - Historical flooding zone' },
  ]
}

export default function RiskMap({ incidentType }: RiskMapProps) {
  const [riskZones, setRiskZones] = useState<any[]>([])
  
  useEffect(() => {
    // In a real app, we would fetch from the API based on incidentType
    if (incidentType === 'all') {
      setRiskZones([
        ...dummyRiskData.crime,
        ...dummyRiskData.fire,
        ...dummyRiskData.flood
      ])
    } else {
      setRiskZones(dummyRiskData[incidentType as keyof typeof dummyRiskData] || [])
    }
  }, [incidentType])

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high':
        return { color: 'red', fillColor: 'rgba(239, 68, 68, 0.7)' }
      case 'medium':
        return { color: 'orange', fillColor: 'rgba(249, 115, 22, 0.7)' }
      case 'low':
        return { color: 'green', fillColor: 'rgba(16, 185, 129, 0.7)' }
      default:
        return { color: 'gray', fillColor: 'rgba(156, 163, 175, 0.7)' }
    }
  }
 

  
  const [gridData, setGridData] = useState(null);
  const [selectedRiskType, setSelectedRiskType] = useState('flood_risk');
  
  useEffect(() => {
    // Load the grid GeoJSON
    axios.get('/singapore-grid-cells.geojson')
      .then((response: { data: SetStateAction<null> }) => {
        setGridData(response.data);
      })
      .catch((error: any) => console.error('Error loading grid data:', error));
  }, []);
  
  // Style function for GeoJSON features
  const styleGridCell = (feature: { properties: { [x: string]: any } }) => {
    if (!feature.properties || !feature.properties[selectedRiskType]) {
      return { fillOpacity: 0 };
    }
    
    const riskScore = feature.properties[selectedRiskType];
    
    // Choose color based on risk type
    let colorScale;
    if (selectedRiskType === 'flood_risk') {
      // Blues for flood
      colorScale = (riskScore: number) => {
        return riskScore < 0.3 ? '#ccffcc' :
               riskScore < 0.5 ? '#aaddff' :
               riskScore < 0.7 ? '#5599ff' :
               riskScore < 0.9 ? '#0055dd' :
               '#0000aa';
      };
    } else if (selectedRiskType === 'fire_risk') {
      // Reds for fire
      colorScale = (riskScore: number) => {
        return riskScore < 0.3 ? '#ccffcc' :
               riskScore < 0.5 ? '#ffff99' :
               riskScore < 0.7 ? '#ffcc44' :
               riskScore < 0.9 ? '#ff5500' :
               '#aa0000';
      };
    } else {
      // Purples for crime
      colorScale = (riskScore: number) => {
        return riskScore < 0.3 ? '#ccffcc' :
               riskScore < 0.5 ? '#cc99ff' :
               riskScore < 0.7 ? '#9944ff' :
               riskScore < 0.9 ? '#6600cc' :
               '#330066';
      };
    }
    
    return {
      fillColor: colorScale(riskScore),
      weight: 0,
      opacity: 0.8,
      color: 'white',
      fillOpacity: 0.6 * riskScore + 0.2  // Higher risk = more opaque
    };
  };

   
  return (
    <div className="map-container">
      <MapContainer
        center={[1.3521, 103.8198]} // Singapore coordinates
        zoom={12}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
       {gridData && (
          <GeoJSON 
            data={gridData}
            style={styleGridCell}
            onEachFeature={(feature, layer) => {
              // Add popup with risk information
              if (feature.properties) {
                layer.bindPopup(`
                  <strong>Grid: ${feature.properties.grid_id || 'Unknown'}</strong><br>
                  Flood Risk: ${(feature.properties.flood_risk * 100).toFixed(1)}%<br>
                  Fire Risk: ${(feature.properties.fire_risk * 100).toFixed(1)}%<br>
                  Crime Risk: ${(feature.properties.crime_risk * 100).toFixed(1)}%
                `);
              }
            }}
          />
        )} 
        {riskZones.map((zone) => {
          const { color, fillColor } = getRiskColor(zone.risk)
          
          return (
            <Rectangle
              key={zone.id}
              bounds={zone.bounds as any}
              pathOptions={{
                color,
                fillColor,
                fillOpacity: 0.0,
                weight: 0
              }}
            >
              <Popup>
                <div>
                  <h3 className="font-semibold capitalize">{zone.risk} Risk Zone</h3>
                  <p className="text-sm">{zone.details}</p>
                </div>
              </Popup>
            </Rectangle>
          )
        })}
      </MapContainer>
    </div>
  )
}
