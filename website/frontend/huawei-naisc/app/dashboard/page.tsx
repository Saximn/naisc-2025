'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Sidebar from '../components/Sidebar'
import RiskSummary from '../components/RiskSummary'
import AlertsList from '../components/AlertsList'

// Import map component dynamically to prevent SSR issues with Leaflet
const RiskMap = dynamic(() => import('../components/RiskMap'), { 
  ssr: false 
})

export default function Dashboard() {
  const [incidentType, setIncidentType] = useState('all')
  const [loading, setLoading] = useState(true)
  const [riskData, setRiskData] = useState({
    crime: { high: 3, medium: 7, low: 12 },
    fire: { high: 2, medium: 5, low: 15 },
    flood: { high: 1, medium: 4, low: 17 }
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
    },
    {
      id: 3,
      type: 'flood',
      severity: 'medium',
      location: 'Lower Kent Ridge Road',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      details: 'High rainfall levels, 76% confidence'
    }
  ])

  // Simulating API fetch
  useEffect(() => {
    // In a real app, we would fetch from the backend
    setTimeout(() => {
      setLoading(false)
    }, 1000)
  }, [])

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
              <RiskMap incidentType={incidentType} />
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
