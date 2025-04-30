'use client'

interface Alert {
  id: number
  type: string
  severity: string
  location: string
  timestamp: string
  details: string
}

interface AlertsListProps {
  alerts: Alert[]
}

export default function AlertsList({ alerts }: AlertsListProps) {
  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'crime':
        return '🚨'
      case 'fire':
        return '🔥'
      case 'flood':
        return '🌊'
      default:
        return '⚠️'
    }
  }

  const getSeverityClass = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'medium':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="space-y-3">
      {alerts.length === 0 ? (
        <div className="p-4 text-center text-gray-500">
          No alerts to display
        </div>
      ) : (
        alerts.map(alert => (
          <div 
            key={alert.id}
            className={`border rounded-lg p-3 ${getSeverityClass(alert.severity)}`}
          >
            <div className="flex items-start">
              <div className="text-2xl mr-3">
                {getAlertIcon(alert.type)}
              </div>
              <div className="flex-grow">
                <div className="flex justify-between items-start">
                  <h4 className="font-semibold capitalize">
                    {alert.type} Alert
                  </h4>
                    <span className="text-xs">
                    {new Date(alert.timestamp).toLocaleString()}
                    </span>
                </div>
                <p className="text-sm mb-1">{alert.location}</p>
                <p className="text-xs">{alert.details}</p>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
