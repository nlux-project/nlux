import config from '../../config/config'
import { IOrderedItems, ISearchResults } from '../../types/ISearchResults'
import { ITransformedData } from '../../types/ITimelines'

export const productionDateCriteria = {
  producedBy: {
    id: `${config.env.dataApiBaseUrl}data/person/mock-person-1`,
  },
}

export const workDateCriteria = {
  OR: [
    {
      createdBy: {
        id: `${config.env.dataApiBaseUrl}data/person/mock-person-1`,
      },
    },
    {
      publishedBy: {
        id: `${config.env.dataApiBaseUrl}data/person/mock-person-1`,
      },
    },
  ],
}

// Each facet value id is a full search URL, as returned by the API; the
// TimelineParser extracts the query params from it.

export const itemProductionDateFacets: Array<IOrderedItems> = [
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221983-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221983-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1983-01-01T00:00:00Z',
    totalItems: 22,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221980-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221980-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1980-01-01T00:00:00Z',
    totalItems: 19,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221977-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221977-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1977-01-01T00:00:00Z',
    totalItems: 18,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221974-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221974-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1974-01-01T00:00:00Z',
    totalItems: 17,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221982-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221982-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1982-01-01T00:00:00Z',
    totalItems: 15,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221976-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221976-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1976-01-01T00:00:00Z',
    totalItems: 12,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221985-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221985-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1985-01-01T00:00:00Z',
    totalItems: 12,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221986-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221986-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1986-01-01T00:00:00Z',
    totalItems: 12,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221971-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221971-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1971-01-01T00:00:00Z',
    totalItems: 11,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221972-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221972-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1972-01-01T00:00:00Z',
    totalItems: 10,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221984-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221984-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1984-01-01T00:00:00Z',
    totalItems: 10,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221981-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221981-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1981-01-01T00:00:00Z',
    totalItems: 8,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221979-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221979-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1979-01-01T00:00:00Z',
    totalItems: 4,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221964-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221964-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1964-01-01T00:00:00Z',
    totalItems: 3,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221968-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221968-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1968-01-01T00:00:00Z',
    totalItems: 3,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221958-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221958-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1958-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221967-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221967-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1967-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221978-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221978-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1978-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221987-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221987-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1987-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221945-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221945-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1945-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221959-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221959-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1959-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221966-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221966-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1966-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221973-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221973-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1973-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221998-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221998-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1998-01-01T00:00:00Z',
    totalItems: 1,
  },
]

export const workCreationDateFacets: Array<IOrderedItems> = [
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221983-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221983-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1983-01-01T00:00:00Z',
    totalItems: 5,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221980-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221980-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1980-01-01T00:00:00Z',
    totalItems: 3,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221977-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221977-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1977-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221974-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221974-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1974-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221982-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221982-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1982-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221976-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221976-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1976-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221985-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221985-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1985-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221986-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221986-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1986-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221971-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221971-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1971-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221972-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221972-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1972-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221984-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221984-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1984-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221981-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221981-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1981-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221979-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221979-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1979-01-01T00:00:00Z',
    totalItems: 1,
  },
]

export const workPublicationDateFacets: Array<IOrderedItems> = [
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221982-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221982-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1982-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221976-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221976-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1976-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221985-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221985-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1985-01-01T00:00:00Z',
    totalItems: 2,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221986-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221986-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1986-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221971-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221971-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1971-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221972-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221972-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1972-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221984-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221984-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1984-01-01T00:00:00Z',
    totalItems: 1,
  },
  {
    id: `${config.env.dataApiBaseUrl}api/search/item?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221981-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221981-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    type: 'OrderedCollection',
    value: '1981-01-01T00:00:00Z',
    totalItems: 1,
  },
]

export const timelineResults: Array<{ [key: string]: ISearchResults }> = [
  {
    'https://endpoint.yale.edu/api/facets/item?q=%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D&name=itemProductionDate':
      {
        '@context': 'test',
        id: 'uri',
        type: 'OrderedCollectionPage',
        orderedItems: itemProductionDateFacets,
        next: {
          id: 'id',
          type: 'OrderedCollectionPage',
        },
      },
  },
  {
    'https://endpoint.yale.edu/api/facets/work?q=%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D&name=workCreationDate':
      {
        '@context': 'test',
        id: 'uri',
        type: 'OrderedCollectionPage',
        orderedItems: workCreationDateFacets,
        next: {
          id: 'id',
          type: 'OrderedCollectionPage',
        },
      },
  },
  {
    'https://endpoint.yale.edu/api/facets/work?q=%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D&name=workPublicationDate':
      {
        '@context': 'test',
        id: 'uri',
        type: 'OrderedCollectionPage',
        orderedItems: workPublicationDateFacets,
        next: {
          id: 'id',
          type: 'OrderedCollectionPage',
        },
      },
  },
]

export const itemProductionDateFacetsTransformed: Array<ITransformedData> = [
  {
    value: '1983',
    totalItems: 22,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221983-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221983-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1980',
    totalItems: 19,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221980-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221980-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1977',
    totalItems: 18,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221977-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221977-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1974',
    totalItems: 17,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221974-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221974-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1982',
    totalItems: 15,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221982-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221982-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1976',
    totalItems: 12,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221976-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221976-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1985',
    totalItems: 12,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221985-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221985-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1986',
    totalItems: 12,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221986-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221986-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1971',
    totalItems: 11,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221971-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221971-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1972',
    totalItems: 10,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221972-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221972-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1984',
    totalItems: 10,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221984-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221984-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1981',
    totalItems: 8,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221981-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221981-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1979',
    totalItems: 4,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221979-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221979-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1964',
    totalItems: 3,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221964-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221964-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1968',
    totalItems: 3,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221968-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221968-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1958',
    totalItems: 2,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221958-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221958-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1967',
    totalItems: 2,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221967-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221967-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1978',
    totalItems: 2,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221978-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221978-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1987',
    totalItems: 2,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221987-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221987-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1945',
    totalItems: 1,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221945-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221945-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1959',
    totalItems: 1,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221959-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221959-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1966',
    totalItems: 1,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221966-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221966-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1973',
    totalItems: 1,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221973-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221973-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
  {
    value: '1998',
    totalItems: 1,
    searchTag: 'itemProductionDate',
    id: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221998-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221998-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
  },
]

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const transformedTimelineFacets: any = {
  '1945': {
    total: 1,
    itemProductionDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221945-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221945-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1958': {
    total: 2,
    itemProductionDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221958-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221958-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1959': {
    total: 1,
    itemProductionDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221959-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221959-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1964': {
    total: 3,
    itemProductionDate: {
      totalItems: 3,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221964-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221964-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1966': {
    total: 1,
    itemProductionDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221966-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221966-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1967': {
    total: 2,
    itemProductionDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221967-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221967-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1968': {
    total: 3,
    itemProductionDate: {
      totalItems: 3,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221968-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221968-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1971': {
    total: 13,
    itemProductionDate: {
      totalItems: 11,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221971-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221971-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221971-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221971-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workPublicationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221971-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221971-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1972': {
    total: 12,
    itemProductionDate: {
      totalItems: 10,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221972-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221972-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221972-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221972-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workPublicationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221972-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221972-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1973': {
    total: 1,
    itemProductionDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221973-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221973-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1974': {
    total: 19,
    itemProductionDate: {
      totalItems: 17,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221974-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221974-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221974-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221974-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1976': {
    total: 16,
    itemProductionDate: {
      totalItems: 12,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221976-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221976-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221976-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221976-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workPublicationDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221976-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221976-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1977': {
    total: 20,
    itemProductionDate: {
      totalItems: 18,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221977-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221977-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221977-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221977-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1978': {
    total: 2,
    itemProductionDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221978-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221978-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1979': {
    total: 5,
    itemProductionDate: {
      totalItems: 4,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221979-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221979-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221979-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221979-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1980': {
    total: 22,
    itemProductionDate: {
      totalItems: 19,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221980-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221980-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 3,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221980-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221980-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1981': {
    total: 10,
    itemProductionDate: {
      totalItems: 8,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221981-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221981-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221981-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221981-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workPublicationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221981-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221981-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1982': {
    total: 19,
    itemProductionDate: {
      totalItems: 15,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221982-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221982-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221982-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221982-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workPublicationDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221982-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221982-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1983': {
    total: 27,
    itemProductionDate: {
      totalItems: 22,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221983-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221983-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 5,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221983-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221983-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1984': {
    total: 12,
    itemProductionDate: {
      totalItems: 10,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221984-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221984-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221984-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221984-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workPublicationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221984-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221984-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1985': {
    total: 15,
    itemProductionDate: {
      totalItems: 12,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221985-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221985-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221985-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221985-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workPublicationDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221985-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221985-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1986': {
    total: 14,
    itemProductionDate: {
      totalItems: 12,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221986-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221986-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workCreationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22createdDate%22%3A%221986-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22createdDate%22%3A%221986-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
    workPublicationDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22OR%22%3A%5B%7B%22createdBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22publishedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%5D%7D%2C%7B%22publishedDate%22%3A%221986-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22publishedDate%22%3A%221986-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1987': {
    total: 2,
    itemProductionDate: {
      totalItems: 2,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221987-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221987-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
  '1998': {
    total: 1,
    itemProductionDate: {
      totalItems: 1,
      searchParams: `?q=%7B%22AND%22%3A%5B%7B%22producedBy%22%3A%7B%22id%22%3A%22https%3A%2F%2Fendpoint.yale.edu%2Fdata%2Fperson%2Fmock-person-1%22%7D%7D%2C%7B%22producedDate%22%3A%221998-12-31T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3C%3D%22%7D%2C%7B%22producedDate%22%3A%221998-01-01T00%3A00%3A00.000Z%22%2C%22_comp%22%3A%22%3E%3D%22%7D%5D%7D`,
    },
  },
}
