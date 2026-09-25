import { render, screen } from '@testing-library/react'
import React from 'react'
import { Provider } from 'react-redux'
import { vi } from 'vitest'

import { entity as mockEntity } from '../../../data/entity'
import { person as mockPerson } from '../../../data/person'
import { store } from '../../../../app/store'
import EntityHeader from '../../../../features/common/EntityHeader'

vi.mock('../../../../redux/api/ml_api', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('../../../../redux/api/ml_api')>()
  return {
    ...actual,
    useGetItemQuery: () => ({
      data: mockPerson,
      isSuccess: true,
    }),
    useGetNameQuery: () => ({
      data: mockPerson,
      isSuccess: true,
    }),
  }
})

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useLocation: () => ({
      pathname: 'mock-path',
    }),
  }
})

describe('EntityHeader', () => {
  it('renders the title', () => {
    render(
      <Provider store={store}>
        <EntityHeader
          entity={mockEntity}
          primaryAgent=""
          start="2000"
          end="2024"
        />
      </Provider>,
    )

    const date = screen.getByTestId('entity-header')
    expect(date).toHaveTextContent('Mock Entity')
  })

  it('renders the icon', () => {
    render(
      <Provider store={store}>
        <EntityHeader
          entity={mockEntity}
          primaryAgent=""
          start="2000"
          end="2024"
        />
      </Provider>,
    )

    const img = screen.getByTestId('entity-icon-img')
    expect(img).toBeInTheDocument()
  })
})
