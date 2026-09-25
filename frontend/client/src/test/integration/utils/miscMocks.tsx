import nock from 'nock'

import { facetNamesLists } from '../../../config/facets'
import { searchScope } from '../../../config/searchTypes'
import config from '../../../config/config'

export default function miscMocks(): void {
  const apiBaseUrl = config.env.dataApiBaseUrl || ''
  const query =
    '?q=%7B%22AND%22%3A%5B%7B%22text%22%3A%22andy%22%2C%22_lang%22%3A%22en%22%7D%2C%7B%22text%22%3A%22warhol%22%2C%22_lang%22%3A%22en%22%7D%5D%7D'

  // Mock facets for all tabs (scope endpoint per tab); date facets are
  // requested with sort=asc
  for (const tab of Object.keys(facetNamesLists)) {
    for (const facet of facetNamesLists[tab]) {
      nock(apiBaseUrl)
        .get(
          `/api/facets/${searchScope[tab]}${query}&name=${facet}${
            facet.includes('Date') ? '&sort=asc' : ''
          }&page=1`,
        )
        .reply(200, JSON.stringify(null), {
          'Access-Control-Allow-Origin': '*',
          'Content-type': 'application/json',
        })
    }
  }
}
