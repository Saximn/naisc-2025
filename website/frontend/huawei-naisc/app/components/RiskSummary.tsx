'use client'

interface RiskSummaryProps {
  title: string
  data: {
    high: number
    medium: number
    low: number
  }
}

export default function RiskSummary({ title, data }: RiskSummaryProps) {
  const total = data.high + data.medium + data.low
  
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-semibold mb-3">{title}</h3>
      
      <div className="flex items-center mb-2">
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div 
            className="h-4 rounded-full flex"
            style={{ 
              background: 'linear-gradient(to right, rgba(239, 68, 68, 0.7), rgba(249, 115, 22, 0.7), rgba(16, 185, 129, 0.7))'
            }}
          ></div>
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-2 text-center mb-1">
        <div>
          <div className="font-semibold text-lg text-red-500">{data.high}</div>
          <div className="text-xs text-gray-500">High Risk</div>
        </div>
        <div>
          <div className="font-semibold text-lg text-orange-500">{data.medium}</div>
          <div className="text-xs text-gray-500">Medium Risk</div>
        </div>
        <div>
          <div className="font-semibold text-lg text-green-500">{data.low}</div>
          <div className="text-xs text-gray-500">Low Risk</div>
        </div>
      </div>
      
      <div className="text-xs text-gray-500 text-center">
        {total} zones monitored
      </div>
    </div>
  )
}
