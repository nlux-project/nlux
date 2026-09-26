// Partner institutions of Collectie NH. Each institution card on the
// landing page links to a full-text search for the institution name,
// which matches the institution labels indexed in the records
// (current_owner / member_of labels in search_text).

export interface IInstitution {
  // Display name of the institution
  name: string
  // Full-text search term that matches this institution's records
  searchTerm: string
}

export const institutions: IInstitution[] = [
  { name: 'Teylers Museum', searchTerm: 'Teylers Museum' },
  { name: 'Noord-Hollands Archief', searchTerm: 'Noord-Hollands Archief' },
  { name: 'Frans Hals Museum', searchTerm: 'Frans Hals Museum' },
  { name: 'Huis van Hilde', searchTerm: 'Huis van Hilde' },
  { name: 'Rijksmuseum Boerhaave', searchTerm: 'Rijksmuseum Boerhaave' },
  { name: 'Rijksmuseum', searchTerm: 'Rijksmuseum' },
  { name: 'Westfries Museum', searchTerm: 'Westfries Museum' },
]

// Quick-search chips shown under the landing page search field.
export const quickSearches: { label: string; term: string }[] = [
  { label: 'Prenten', term: 'prent' },
  { label: 'Tekeningen', term: 'tekening' },
  { label: 'Schilderijen', term: 'schilderij' },
  { label: "Foto's", term: 'foto' },
]

// Build a results-page URL that runs a simple full-text search,
// mirroring the query that the search box itself produces
// (q from the translate endpoint, sq for the input display value).
export const fullTextSearchUrl = (term: string): string => {
  const params = new URLSearchParams()
  params.set('q', JSON.stringify({ text: term, _lang: 'en' }))
  params.set('sq', term)
  return `/view/results/objects?${params.toString()}`
}

export const institutionSearchUrl = fullTextSearchUrl
