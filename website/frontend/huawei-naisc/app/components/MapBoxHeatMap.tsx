// app/components/MapboxHeatmap.tsx
'use client'

import mapboxgl from 'mapbox-gl'
import { MapboxInterpolateHeatmapLayer } from 'mapbox-gl-interpolate-heatmap'
import { useEffect } from 'react'

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!

export default function MapboxHeatmap({ incidentType }: { incidentType: string }) {
  useEffect(() => {
    const map = new mapboxgl.Map({
      container: 'map',
      center: [103.8198, 1.3521],
      zoom: 11,
      style: 'mapbox://styles/mapbox/light-v10',
    });

    const tempDataFire = Array.from({ length: 400 }, () => ({
      lat: 1.2 + Math.random() * 0.4, // Latitude within Singapore range
      lon: 103.6 + Math.random() * 0.5, // Longitude within Singapore range
      val: Math.random(), // Random value between 0 and 1
    }));

    const tempDataCrime = Array.from({ length: 400 }, () => ({
      lat: 1.2 + Math.random() * 0.4, // Latitude within Singapore range
      lon: 103.6 + Math.random() * 0.5, // Longitude within Singapore range
      val: Math.random(), // Random value between 0 and 1
    }));

    const tempDataFlood = Array.from({ length: 400 }, () => ({
      lat: 1.2 + Math.random() * 0.4, // Latitude within Singapore range
      lon: 103.6 + Math.random() * 0.5, // Longitude within Singapore range
      val: Math.random(), // Random value between 0 and 1
    }));

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

    map.on('load', () => {
      map.addControl(new mapboxgl.NavigationControl(), 'top-right');
      const layer = new MapboxInterpolateHeatmapLayer({
        id: 'temperature',
        data: incidentType === 'fire' ? tempDataFire : incidentType === 'crime' ? tempDataCrime : incidentType === 'flood' ? tempDataFlood : tempDataFlood,
        aoi: aoidata
      });
      map.addLayer(layer, 'road-label');
      map.addSource('places', {
        'type': 'geojson',
        'data': {
            'type': 'FeatureCollection',
            'features': [
                {
                    'type': 'Feature',
                    'properties': {
                        'description':
                            '<strong>High Flood Risk</strong><p>Confidence: 90%</p>'
                    },
                    'geometry': {
                        'type': 'Point',
                        
                        'coordinates': [103.9227, 1.3391]
                    }
                },
              ]
            }})
            map.addLayer({
              'id': 'places',
              'type': 'circle',
              'source': 'places',
              'paint': {
                'circle-color': '#ff0000',
                'circle-radius': incidentType === 'flood' ? 10 : 0,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff'
              }
            }, 'temperature');
          // Create a popup, but don't add it to the map yet.
        const popup = new mapboxgl.Popup({
          closeButton: false,
          closeOnClick: false
      });map.on('mouseenter', 'places', (e) => {
            // Change the cursor style as a UI indicator.
            map.getCanvas().style.cursor = 'pointer';

            // Copy coordinates array.
            const coordinates = e.features[0].geometry.coordinates.slice();
            const description = e.features[0].properties.description;

            // Ensure that if the map is zoomed out such that multiple
            // copies of the feature are visible, the popup appears
            // over the copy being pointed to.
            if (['mercator', 'equirectangular'].includes(map.getProjection().name)) {
                while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
                    coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
                }
            }

            // Populate the popup and set its coordinates
            // based on the feature found.
            popup.setLngLat(coordinates).setHTML(description).addTo(map);
        });
      map.on('mouseleave', 'places', () => {
        map.getCanvas().style.cursor = '';
        popup.remove();
    });
    });

    

    return () => map.remove();
  }, [incidentType]);

  return <div id="map" className="h-full w-full" />
}
