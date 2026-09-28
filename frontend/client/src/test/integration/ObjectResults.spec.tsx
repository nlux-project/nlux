import { cleanup, render, screen } from '@testing-library/react'
import React from 'react'
import { vi } from 'vitest'

import objectMockApi from './utils/objectResultsMockAPI'
import AppRender from './utils/AppRender'
import cmsMockApi from './utils/cmsMockApi'
import estimatesMockApi from './utils/estimatesMockApi'
import eventTrackingMock from './utils/eventTrackingMock'

// Mock the request for collections
vi.mock('../../lib/util/collectionHelper', () => ({
  __esModule: true,
  getCollections: vi.fn(() => ({
    data: [
      'https://endpoint.yale.edu/data/set/member-of-collection-1',
      'https://endpoint.yale.edu/data/set/member-of-collection-2',
    ],
  })),
}))

describe('Object results page', () => {
  const page =
    '/view/results/objects?q=%7B"AND"%3A%5B%7B"text"%3A"andy"%2C"_lang"%3A"en"%7D%2C%7B"text"%3A"warhol"%2C"_lang"%3A"en"%7D%5D%7D&sq=andy+warhol'

  beforeEach(async () => {
    objectMockApi()
    estimatesMockApi()
    cmsMockApi()
    eventTrackingMock()
  })

  describe('Results header', () => {
    it('renders the correct title', async () => {
      render(<AppRender route={page} />)

      const title = await screen.findByTestId('results-header-title')
      expect(title).toHaveTextContent('801 resultaten')
    })

    it('renders the correct results descriptor', async () => {
      render(<AppRender route={page} />)

      await screen.findByTestId('results-header-title')
      await screen.findByText(/Description of the objects results\./)
      const descriptor = screen.getByTestId('results-page-cms-descriptor')
      expect(descriptor).toHaveTextContent(
        'Description of the objects results.',
      )
    })

    it('renders the grid view button', async () => {
      render(<AppRender route={page} />)

      await screen.findByTestId('results-header-title')
      const button = screen.getByTestId('switch-to-grid-view-button')
      expect(button).toBeInTheDocument()
    })
  })

  describe('Object results grid view', () => {
    const gridViewPage =
      '/view/results/objects?q=%7B"AND"%3A%5B%7B"text"%3A"andy"%2C"_lang"%3A"en"%7D%2C%7B"text"%3A"warhol"%2C"_lang"%3A"en"%7D%5D%7D&sq=andy+warhol&view=grid'

    it('renders the list view button', async () => {
      render(<AppRender route={gridViewPage} />)

      await screen.findByTestId('results-header-title')
      const button = screen.getByTestId('switch-to-list-view-button')
      expect(button).toBeInTheDocument()
    })

    it('renders the object title', async () => {
      const { findAllByText } = render(<AppRender route={gridViewPage} />)

      await findAllByText(/Mock Object/i)
      const title = screen.getByTestId('grid-view-object-results-snippet-title')
      expect(title).toHaveTextContent('Mock Object')
    })

    it('renders the event agent', async () => {
      render(<AppRender route={gridViewPage} />)

      const agent = screen.getByTestId('grid-view-object-event-agent')
      expect(agent).toBeInTheDocument()
    })

    it('renders the event dates', async () => {
      render(<AppRender route={gridViewPage} />)

      const dates = screen.getByTestId('grid-view-event-date')
      expect(dates).toBeInTheDocument()
    })

    it('renders the icon if no image is available in grid view', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)
      const icon = screen.getByTestId('results-snippet-icon')
      expect(icon).toBeInTheDocument()
    })
  })

  describe('SortDropdown', () => {
    it('renders the correct dropdown options', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)

      const sortDropdown = screen.getByTestId('results-sort-dropdown')
      expect(sortDropdown).toBeInTheDocument()
      const options = screen.getAllByTestId('results-sort-option')
      expect(options.length).toBe(3)
      expect(options[0]).toHaveTextContent('Relevantie')
      expect(options[1]).toHaveTextContent('Titel A–Z')
      expect(options[2]).toHaveTextContent('Nieuwste eerst')
    })
  })

  describe('ObjectSnippet', () => {
    it('renders the title with the link to the record', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)
      const header = screen.getByTestId('object-results-snippet-title')
      expect(header).toHaveTextContent('Mock Object')
    })

    it('renders event agent and date', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)
      const producedBy = screen.getByTestId('production-snippet-agent-data')
      expect(producedBy).toHaveTextContent('Mock Person in 1891')
    })

    it('renders event location', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)
      const productionPlace = screen.getByTestId(
        'production-snippet-location-data',
      )
      expect(productionPlace).toBeInTheDocument()
    })

    it('renders object types', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)
      const header = screen.getByTestId('entity-type-list')
      expect(header).toBeInTheDocument()
    })

    it('renders the collections', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)
      const collections = screen.getByTestId('object-snippet-collections')
      expect(collections).toBeInTheDocument()
    })

    it('renders the call number', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)
      const identifiers = screen.getByTestId('object-snippet-identifiers')
      expect(identifiers).toHaveTextContent('Mock Call Number')
    })

    it('renders the icon if no image is available', async () => {
      const { findAllByText } = render(<AppRender route={page} />)

      await findAllByText(/Mock Object/i)
      const icon = screen.getByTestId('results-snippet-icon')
      expect(icon).toBeInTheDocument()
    })
  })

  afterEach(cleanup)
})
