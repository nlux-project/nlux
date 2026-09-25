import { render, screen } from '@testing-library/react'
import React from 'react'
import { AuthProvider } from 'react-oidc-context'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'

import RelatedObjectsWorksAndCollections from '../../../../features/common/RelatedObjectsWorksAndCollections'
import { entity as mockEntity } from '../../../data/entity'
import ILinks from '../../../../types/data/ILinks'
import { store } from '../../../../app/store'

const mockRelationships = {
  objects: {
    title: 'Related Objects',
    searchTag: 'lux:relatedObjectsSearchTag',
    tab: 'objects',
  },
}

describe('RelatedObjectsWorksAndCollections', () => {
  it('renders the error message', async () => {
    render(
      <Provider store={store}>
        <BrowserRouter>
          <AuthProvider
            authority="dummy"
            client_id="dummy"
            redirect_uri="dummy"
            response_type="code"
            scope="openid email"
          >
            <RelatedObjectsWorksAndCollections
              links={mockEntity._links as ILinks}
              relationships={mockRelationships}
              type="event"
            />
          </AuthProvider>
        </BrowserRouter>
      </Provider>,
    )

    const message = screen.getByTestId('no-related-objects-works')
    expect(message).toHaveTextContent(
      'We do not have any objects or works directly related to this event.',
    )
  })
})
