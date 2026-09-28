import nock from 'nock'

import config from '../../../config/config'
import { activityStreams } from '../../data/results'
import { IOrderedItems } from '../../../types/ISearchResults'

/**
 * Mocks the requests made by the highlights ("Uitgelicht") section on the
 * landing page: a search for records with images plus the record requests
 * for each of the returned items.
 */
export default function highlightsMockApi(): void {
  const apiUrl = config.env.dataApiBaseUrl || ''
  const mockObjectUri = 'data/object/highlight-object'

  // Mock the image records search made by the highlights section. The
  // search stubs include labels so the section can screen its candidates.
  const searchResponse = activityStreams(mockObjectUri, 4)
  searchResponse.orderedItems = [
    {
      id: `${apiUrl}${mockObjectUri}`,
      type: 'HumanMadeObject',
      label: 'Mock Highlight',
    } as IOrderedItems,
  ]

  nock(apiUrl)
    .get('/api/search/item?q=%7B%22hasDigitalImage%22%3A1%7D&page=1')
    .reply(200, JSON.stringify(searchResponse), {
      'Access-Control-Allow-Origin': '*',
      'Content-type': 'application/json',
    })

  // Mock the record request for the highlighted object, including an image
  const highlightObject = {
    id: `${apiUrl}${mockObjectUri}`,
    type: 'HumanMadeObject',
    _label: 'Mock Highlight',
    representation: [
      {
        id: `${apiUrl}data/visualitem/highlight-image`,
        type: 'VisualItem',
        _label: 'Highlight Image',
        digitally_shown_by: [
          {
            id: 'https://iiif.test.org/highlight-image',
            type: 'DigitalObject',
          },
        ],
      },
    ],
    current_owner: [
      {
        id: `${apiUrl}data/group/mock-institution`,
        type: 'Group',
        _label: 'Mock Institution',
      },
    ],
  }

  nock(apiUrl)
    .get('/data/object/highlight-object?profile=results')
    .reply(200, JSON.stringify(highlightObject), {
      'Access-Control-Allow-Origin': '*',
      'Content-type': 'application/json',
    })
}
