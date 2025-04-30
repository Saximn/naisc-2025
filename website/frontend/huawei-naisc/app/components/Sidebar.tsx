'use client'

import Link from 'next/link'
import { useState } from 'react'

interface SidebarProps {
  activeSection: string
  onFilterChange?: (filter: string) => void
}

export default function Sidebar({ activeSection, onFilterChange }: SidebarProps) {
  const [filter, setFilter] = useState('flood')

  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter)
    if (onFilterChange) {
      onFilterChange(newFilter)
    }
  }

  return (
    <aside className="sidebar">
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-2">PERS</h2>
        <p className="text-sm text-blue-200">Predictive Emergency Response System</p>
      </div>

      <nav className="mb-8">
        <ul className="space-y-2">
          <li>
            <Link href="/dashboard" className={`block py-2 px-4 rounded ${activeSection === 'dashboard' ? 'bg-blue-700' : 'hover:bg-blue-700'}`}>
              Dashboard
            </Link>
          </li>
        </ul>
      </nav>

      {onFilterChange && (
        <div className="mb-8">
          <h3 className="text-sm uppercase tracking-wider mb-3">Filter Incidents</h3>
          <ul className="space-y-2">
            <li>
              <button 
                onClick={() => handleFilterChange('flood')}
                className={`w-full text-left py-1 px-3 rounded ${filter === 'flood' ? 'bg-blue-600' : 'hover:bg-blue-600'}`}
              >
                Flood
              </button>
            </li>
            <li>
              <button 
                onClick={() => handleFilterChange('crime')}
                className={`w-full text-left py-1 px-3 rounded ${filter === 'crime' ? 'bg-blue-600' : 'hover:bg-blue-600'}`}
              >
                Crime
              </button>
            </li>
            <li>
              <button 
                onClick={() => handleFilterChange('fire')}
                className={`w-full text-left py-1 px-3 rounded ${filter === 'fire' ? 'bg-blue-600' : 'hover:bg-blue-600'}`}
              >
                Fire
              </button>
            </li>
          </ul>
        </div>
      )}

      <div className="mt-auto">
        <div className="bg-blue-800 rounded p-3">
          <h3 className="text-sm font-semibold mb-2">System Status</h3>
          <div className="flex items-center mb-1">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
            <span className="text-sm">Models: Operational</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
            <span className="text-sm">Data Pipeline: Active</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
