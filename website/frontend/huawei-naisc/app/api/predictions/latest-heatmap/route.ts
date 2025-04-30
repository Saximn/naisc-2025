import { NextRequest, NextResponse } from 'next/server'

/**
 * GET handler for getting the latest prediction heatmap data
 */
export async function GET(request: NextRequest) {
  try {
    // Parse downsample factor from URL if provided
    const searchParams = request.nextUrl.searchParams
    const downsampleFactor = searchParams.get('downsample_factor') || '3'
    
    // Get backend URL from environment variables
    const backendUrl = process.env.BACKEND_API_URL
    
    if (!backendUrl) {
      throw new Error('BACKEND_API_URL environment variable is not set')
    }
    
    // Build the full URL for the Django endpoint
    const url = `${backendUrl}/predictions/latest?downsample_factor=${downsampleFactor}`
    
    // Make the request to Django backend
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        // Add any auth headers if needed
        // 'Authorization': `Token ${process.env.API_TOKEN}`
      },
      // Add this to avoid caching issues
      cache: 'no-store',
    })
    
    // If Django returns an error, forward it
    if (!response.ok) {
      return NextResponse.json(
        { error: `Backend returned status ${response.status}` },
        { status: response.status }
      )
    }
    
    // Get data from Django response
    const data = await response.json()
    
    // Forward the response back to the client
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('Error fetching prediction data:', error)
    return NextResponse.json(
      { error: 'Failed to fetch prediction data' },
      { status: 500 }
    )
  }
}