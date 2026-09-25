import { render, screen } from '@testing-library/react'
import React from 'react'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'

import { store } from '../../../../app/store'
import TextContainer from '../../../../features/common/TextContainer'

describe('TextContainer', () => {
  it('renders', async () => {
    render(
      <Provider store={store}>
        <MemoryRouter>
          <TextContainer>
            <p>child</p>
          </TextContainer>
        </MemoryRouter>
      </Provider>,
    )

    const container = screen.getByTestId('text-container')
    expect(container).toBeInTheDocument()
  })

  it('renders children', async () => {
    render(
      <Provider store={store}>
        <MemoryRouter>
          <TextContainer>
            <p data-testid="text-container-child">child</p>
          </TextContainer>
        </MemoryRouter>
      </Provider>,
    )

    const child = screen.getByTestId('text-container-child')
    expect(child).toBeInTheDocument()
  })

  it('renders TextLabel', async () => {
    render(
      <Provider store={store}>
        <MemoryRouter>
          <TextContainer>
            <p>child</p>
          </TextContainer>
        </MemoryRouter>
      </Provider>,
    )

    const label = screen.getByTestId('text-label')
    expect(label).toBeInTheDocument()
  })
})
