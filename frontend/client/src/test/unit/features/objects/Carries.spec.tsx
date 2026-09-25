import { fireEvent, render, screen } from '@testing-library/react'
import React from 'react'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'

import Carries from '../../../../features/objects/Carries'
import { physicalObject as mockObject } from '../../../data/object'
import { store } from '../../../../app/store'

vi.mock('../../../../redux/api/ml_api', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('../../../../redux/api/ml_api')>()
  return {
    ...actual,
    useGetItemQuery: () => ({
      data: mockObject,
      isSuccess: true,
    }),
    useGetNameQuery: () => ({
      data: mockObject,
      isSuccess: true,
    }),
  }
})

describe('Carries', () => {
  it('renders the works snippet', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <Carries entity={mockObject} defaultLength={1} />
        </BrowserRouter>
      </Provider>,
    )

    const carries = screen.getByTestId('work-snippet-list-view')
    expect(carries).toBeInTheDocument()
  })

  it('renders the show all button', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <Carries entity={mockObject} defaultLength={0} />
        </BrowserRouter>
      </Provider>,
    )

    const button = screen.getByTestId('carries-show-all')
    expect(button).toBeInTheDocument()
  })

  it('renders the show less button', () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <Carries entity={mockObject} defaultLength={0} />
        </BrowserRouter>
      </Provider>,
    )

    // Click show all button
    const showAll = screen.getByTestId('carries-show-all')
    fireEvent.click(showAll)

    const button = screen.getByTestId('carries-show-less')
    expect(button).toBeInTheDocument()
  })
})
