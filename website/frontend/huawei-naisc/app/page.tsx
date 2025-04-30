'use client'

import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gradient-to-b from-blue-800 to-blue-900">
      <div className="max-w-5xl w-full bg-white rounded-lg shadow-xl overflow-hidden">
        <div className="md:flex">
          <div className="md:w-1/2 p-8 flex flex-col justify-center">
            <h1 className="text-3xl font-bold text-gray-800 mb-4">
              Singapore Predictive Emergency Response System
            </h1>
            <p className="text-gray-600 mb-6">
              Empowering Singapore to shift from reactive to proactive incident management by forecasting high-risk zones for crime, fire, and flash floods.
            </p>
            <div className="space-y-4">
              <button 
                onClick={() => router.push('/dashboard')}
                className="w-full py-2 px-4 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75"
              >
                Access Dashboard
              </button>
              <button className="w-full py-2 px-4 border border-gray-300 text-gray-700 font-semibold rounded-lg shadow-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-200 focus:ring-opacity-75">
                Learn More
              </button>
            </div>
          </div>
          <div className="md:w-1/2 bg-gray-100 flex items-center justify-center p-8">
            <div className="w-full h-64 relative bg-gray-200 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <Image
                  src="/images/homepage-hero.png"
                  alt="Predictive Emergency Response System"
                  layout="fill"
                  objectFit="cover"
                ></Image>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-gray-50 px-8 py-4">
          <div className="flex flex-wrap justify-between items-center">
            <p className="text-sm text-gray-500">© 2025 AISDC - Huawei Track</p>
            <div className="flex space-x-4">
              <span className="text-sm text-gray-500">Powered by AI</span>
              <span className="text-sm text-gray-500">Cloud-Native</span>
              <span className="text-sm text-gray-500">Real-Time Predictions</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
