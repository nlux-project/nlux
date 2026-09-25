import { render, screen } from '@testing-library/react'
import React from 'react'
import { vi } from 'vitest'

import Map from '../../../../features/common/Map'

const mockConfig = {
  thumbnailMode: false,
  wkt: 'POINT (-76.33269 44.38342)',
}

vi.mock('leaflet')

// react-leaflet's real components require a DOM with layout (jsdom cannot
// provide it) — stub them out; the testid under test lives on the app's
// own wrapper element
vi.mock('react-leaflet', () => ({
  GeoJSON: () => null,
  MapContainer: ({ children }: { children?: React.ReactNode }) => (
    <div>{children}</div>
  ),
  Marker: () => null,
  TileLayer: () => null,
}))

describe('Map', () => {
  it('renders', async () => {
    render(<Map config={mockConfig} className="col md" />)

    const map = screen.getByTestId('map-container')
    expect(map).toBeInTheDocument()
  })
})
