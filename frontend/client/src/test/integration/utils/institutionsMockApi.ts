import nock from 'nock'

import config from '../../../config/config'
import { institutions } from '../../../config/institutions'

/**
 * Mocks the search-estimate requests made by the institutions ("Collecties")
 * section on the landing page: one estimate per institution, returning the
 * number of objects held by that institution.
 */
export default function institutionsMockApi(): void {
  const apiUrl = config.env.dataApiBaseUrl || ''

  institutions.forEach((institution, index) => {
    const counts = [200, 408, 400, 400, 0, 0, 400]
    nock(apiUrl)
      .get(
        `/api/search-estimate/item?q=${encodeURIComponent(institution.searchTerm)}`,
      )
      .reply(200, JSON.stringify({ totalItems: counts[index] }), {
        'Access-Control-Allow-Origin': '*',
        'Content-type': 'application/json',
      })
  })
}
