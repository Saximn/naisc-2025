'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Sidebar from '../components/Sidebar'
import RiskSummary from '../components/RiskSummary'
import AlertsList from '../components/AlertsList'

// Import map component dynamically to prevent SSR issues
const RiskMap = dynamic(() => import('../components/RiskMap'), {
  ssr: false
})

export default function Dashboard() {
  const [incidentType, setIncidentType] = useState('flood')
  const [loading, setLoading] = useState(true)
  const [floodData, setFloodData] = useState<any[]>([])
  const [fetchError, setFetchError] = useState<string | null>(null)
  
  const [riskData, setRiskData] = useState({
    crime: { high: 3, medium: 7, low: 12 },
    fire: { high: 2, medium: 5, low: 15 },
    flood: { high: 0, medium: 0, low: 0 }
  })
  
  const [alerts, setAlerts] = useState([
    {
      id: 1,
      type: 'crime',
      severity: 'high',
      location: 'Orchard Road',
      timestamp: new Date().toISOString(),
      details: 'Unusual activity detected, 87% confidence'
    },
    {
      id: 2,
      type: 'fire',
      severity: 'high',
      location: 'Industrial Area B3',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      details: 'Temperature anomaly, 92% confidence'
    }
  ])

  // Fetch latest prediction data and update risk summary
  useEffect(() => {
    const fetchLatestPrediction = async () => {
      try {
        setLoading(true)
        setFetchError(null)
        
        const response = await fetch('/api/predictions/latest-heatmap?downsample_factor=3')
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        
        // Set the flood data points
        setFloodData(data.points || [])
        
        // Count points by risk level
        let high = 0, medium = 0, low = 0
        
        data.points.forEach((point: { val: number }) => {
          if (point.val > 0.7) high++
          else if (point.val > 0.3) medium++
          else low++
        })
        
        // Update risk data
        setRiskData(prevData => ({
          ...prevData,
          flood: { high, medium, low }
        }))
        
        // Create alerts for high-risk areas
        if (high > 0) {
          const highRiskPoints = data.points
            .filter((point: { val: number }) => point.val > 0.7)
            .sort((a: { val: number }, b: { val: number }) => b.val - a.val)
            .slice(0, 3)
          
          const newAlerts = highRiskPoints.map((point: { lat: number, lon: number, val: number }, index: number) => ({
            id: Date.now() + index,
            type: 'flood',
            severity: 'high',
            location: `Area near ${point.lat.toFixed(4)}, ${point.lon.toFixed(4)}`,
            timestamp: new Date().toISOString(),
            details: `High flood risk detected, ${Math.round(point.val * 100)}% confidence`
          }))
          
          setAlerts(prevAlerts => [
            ...newAlerts,
            ...prevAlerts.filter(alert => alert.type !== 'flood').slice(0, 5)
          ])
        }
        
      } catch (error) {
        console.error('Error fetching prediction data:', error)
        setFetchError(error instanceof Error ? error.message : 'Unknown error')
        
        // Generate fallback data if fetching fails
        generateFallbackData()
      } finally {
        setLoading(false)
      }
    }
    
    fetchLatestPrediction()
  }, [])
  
  // Generate fallback data if API call fails
  const generateFallbackData = () => {
    const tempData = Array.from({ length: 400 }, () => ({
      lat: 1.2 + Math.random() * 0.4, // Latitude within Singapore range
      lon: 103.6 + Math.random() * 0.5, // Longitude within Singapore range
      val: Math.random(), // Random value between 0 and 1
    }))
    
    setFloodData(tempData)
  }

  return (
    <div className="dashboard-container">
      <Sidebar activeSection="dashboard" onFilterChange={setIncidentType} />
      
      <main className="main-content">
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">Emergency Response Dashboard</h1>
          <p className="text-gray-600">
            Real-time predictive analysis and risk assessment across Singapore
          </p>
        </div>
        
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              <RiskSummary title="Crime Risk Zones" data={riskData.crime} />
              <RiskSummary title="Fire Risk Zones" data={riskData.fire} />
              <RiskSummary title="Flood Risk Zones" data={riskData.flood} />
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-4 mb-6">
              <h2 className="text-xl font-semibold mb-4">Risk Heatmap</h2>
              {fetchError && (
                <div className="mb-4 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-700 text-sm">
                  Warning: Using fallback data. {fetchError}
                </div>
              )}
              <RiskMap 
                incidentType={incidentType} 
                floodData={floodData}
              />
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-4">
              <h2 className="text-xl font-semibold mb-4">Recent Alerts</h2>
              <AlertsList alerts={alerts} />
            </div>
          </>
        )}
      </main>
    </div>
  )
}