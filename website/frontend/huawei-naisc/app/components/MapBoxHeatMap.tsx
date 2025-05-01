'use client'

import mapboxgl from 'mapbox-gl'
import { MapboxInterpolateHeatmapLayer } from 'mapbox-gl-interpolate-heatmap'
import { useEffect, useRef, useState } from 'react'
import 'mapbox-gl/dist/mapbox-gl.css'

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!

type HeatmapPoint = {
  lat: number
  lon: number
  val: number
}

type MapboxHeatmapProps = {
  incidentType: string
  customData: HeatmapPoint[]
}



export default function MapboxHeatmap({ incidentType, customData }: MapboxHeatmapProps) {
  const map = useRef<mapboxgl.Map | null>(null)
  const mapContainer = useRef<HTMLDivElement | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  
  // Singapore polygon boundary for Area of Interest
  const aoidata = [
    { "lat": 1.26675774823251, "lon": 103.60313415527344 },
    { "lat": 1.3244212231757635, "lon": 103.61755371093749 },
    { "lat": 1.3896342476555246, "lon": 103.65325927734375 },
    { "lat": 1.4143460858068593, "lon": 103.66630554199219 },
    { "lat": 1.4294476354255539, "lon": 103.67179870605467 },
    { "lat": 1.439057660807751, "lon": 103.68278503417969 },
    { "lat": 1.4438626583311722, "lon": 103.69583129882812 },
    { "lat": 1.4589640128389818, "lon": 103.72055053710938 },
    { "lat": 1.4582775898253464, "lon": 103.73771667480469 },
    { "lat": 1.4493540716333067, "lon": 103.75419616699219 },
    { "lat": 1.4500404973607948, "lon": 103.7603759765625 },
    { "lat": 1.4788701887242242, "lon": 103.80363464355467 },
    { "lat": 1.4754381021049132, "lon": 103.8269805908203 },
    { "lat": 1.4582775898253464, "lon": 103.86680603027342 },
    { "lat": 1.4321933610794366, "lon": 103.8922119140625 },
    { "lat": 1.4287612034988086, "lon": 103.89701843261717 },
    { "lat": 1.4267019064882447, "lon": 103.91555786132812 },
    { "lat": 1.4321933610794366, "lon": 103.93478393554688 },
    { "lat": 1.4218968729661605, "lon": 103.96018981933592 },
    { "lat": 1.4246426076343077, "lon": 103.985595703125 },
    { "lat": 1.4212104387885494, "lon": 104.00070190429688 },
    { "lat": 1.4397440896459617, "lon": 104.02130126953125 },
    { "lat": 1.445921939876798, "lon": 104.04396057128906 },
    { "lat": 1.4246426076343077, "lon": 104.08721923828125 },
    { "lat": 1.3971851147344805, "lon": 104.09477233886719 },
    { "lat": 1.3573711816421556, "lon": 104.08103942871094 },
    { "lat": 1.2537146393239096, "lon": 103.98216247558594 },
    { "lat": 1.1754546449158993, "lon": 103.81256103515625 },
    { "lat": 1.1301452152248344, "lon": 103.73634338378906 },
    { "lat": 1.1905576261723045, "lon": 103.65394592285156 },
    { "lat": 1.1960495988987414, "lon": 103.60536865234375 },
    { "lat": 1.26675774823251, "lon": 103.60313415527344 }
  ]

  type LatLng = { lat: number; lon: number };

  // Ray-casting algorithm for point-in-polygon
  function isPointInPolygon(point: LatLng, polygon: LatLng[]): boolean {
    const x = point.lon;
    const y = point.lat;
    let inside = false;

    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const xi = polygon[i].lon, yi = polygon[i].lat;
      const xj = polygon[j].lon, yj = polygon[j].lat;

      const intersect =
        yi > y !== yj > y &&
        x < ((xj - xi) * (y - yi)) / (yj - yi + 0.0000001) + xi;

      if (intersect) inside = !inside;
    }

    return inside;
  }

  // Initialize map once on component mount
  useEffect(() => {
    if (map.current) return; // Skip if already initialized
    
    if (!mapContainer.current) return; // Make sure container exists
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      center: [103.8198, 1.3521],
      zoom: 11,
      style: 'mapbox://styles/mapbox/light-v10',
    })
    console.log(map.current, mapContainer.current)
    
    // Add navigation control
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right')

    // Set flag when map is loaded
    map.current.on('load', () => {
      console.log('Map style loaded')
      setMapLoaded(true)
    })

    // Cleanup on unmount
    return () => {
      if (map.current) {
        map.current.remove()
        map.current = null
      }
    }
  }, [])

  // Update map ONLY after it's loaded and when data changes
  useEffect(() => {
    if (!map.current || !mapLoaded) return

    console.log('Updating map with new data', incidentType)
    
    try {
      // Clean up previous layers
      if (map.current.getLayer('temperature')) {
        map.current.removeLayer('temperature')
      }
      if (map.current.getLayer('places')) {
        map.current.removeLayer('places')
      }
      if (map.current.getSource('places')) {
        map.current.removeSource('places')
      }

      // Add the heatmap layer with provided data
      const layer = new MapboxInterpolateHeatmapLayer({
        id: 'temperature',
        data: customData,
        aoi: aoidata
      })
      
      map.current.addLayer(layer)

      // Add high-risk markers if flood incident type
      if (incidentType === 'flood') {
        // Find highest risk areas (top 3 points with highest values)
        console.log('Custom data:', customData)
        const highRiskPoints = [...customData]
          .sort((a, b) => b.val - a.val)
          .filter((point, index) => isPointInPolygon({ lat: point.lat, lon: point.lon }, aoidata))
          .slice(0, 3)
          .map((point, index) => ({
            type: "Feature" as const,
            properties: {
              description: `<strong>High Flood Risk Zone ${index + 1}</strong><p>Confidence: ${Math.round(point.val * 100)}%</p>`
            },
            geometry: {
              type: "Point" as const,
              coordinates: [point.lon, point.lat]
            }
          }))

          console.log('High risk points:', highRiskPoints)
        map.current.addSource('places', {
          type: 'geojson',
          data: {
            type: 'FeatureCollection',
            features: highRiskPoints
          }
        })

        map.current.addLayer({
          id: 'places',
          type: 'circle',
          source: 'places',
          paint: {
            'circle-color': '#ff0000',
            'circle-radius': 10,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
          }
        })

        // Add popup functionality
        const popup = new mapboxgl.Popup({
          closeButton: false,
          closeOnClick: false
        })

        map.current.on('mouseenter', 'places', (e) => {
          // Change cursor style
          if (map.current) {
            map.current.getCanvas().style.cursor = 'pointer'
          }

          // Get coordinates and description
          // @ts-ignore - TS doesn't recognize features property
          const coordinates = e.features[0].geometry.coordinates.slice()
          // @ts-ignore
          const description = e.features[0].properties.description

          // Ensure popup appears over the feature being pointed to
          if (map.current && ['mercator', 'equirectangular'].includes(map.current.getProjection().name)) {
            while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
              coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360
            }
          }

          // Show popup
          if (map.current) {
            popup.setLngLat(coordinates).setHTML(description).addTo(map.current)
          }
        })

        map.current.on('mouseleave', 'places', () => {
          if (map.current) {
            map.current.getCanvas().style.cursor = ''
          }
          popup.remove()
        })
      }
    } catch (error) {
      console.error('Error updating map:', error)
    }
  }, [mapLoaded, incidentType, customData])

  return <div ref={mapContainer} className="h-full w-full" />
}