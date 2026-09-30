import React, { type JSX } from 'react'

import { ICriteria, IOrderedItems } from '../../types/ISearchResults'
import { IFacetsPagination } from '../../types/IFacets'
import { useAppDispatch } from '../../app/hooks'
import { pushClientEvent } from '../../lib/pushClientEvent'
import { AllowedTypeLabels } from '../../redux/slices/facetsSlice'

interface IFacets {
  criteria: ICriteria
  facetValues: IFacetsPagination
  facetSection: string
  facetQuery: ICriteria
  scope: string
  selectedFacets: Map<string, Set<string>> | null
  page: number
  lastPage: number
  setPage: (x: number) => void
  setFacets: (x: IFacetsPagination) => void
}

const FACET_TYPE_LIMIT = 5

/**
 * Validates and filters selected type facets to only allow predefined labels.
 * @param selectedTypes - Array of selected type values
 * @returns Filtered array of selected types
 */
export const filterSelectedTypes = (selectedTypes: string[]): string[] => {
  const result: string[] = []
  
  for (const type of selectedTypes) {
    if ((typeof AllowedTypeLabels !== 'undefined' && AllowedTypeLabels.includes(type)) || type === 'less...') {
      result.push(type)
    }
  }
  
  return result
}

const Checklist: React.FC<IFacets> = ({
  criteria,
  facetValues,
  facetSection,
  facetQuery,
  scope,
  selectedFacets,
  page,
  lastPage,
  setPage,
  setFacets,
}) => {
  const dispatch = useAppDispatch()

  const handleShowMore = (): void => {
    setPage(page + 1)
    dispatch(addLastSelectedFacet({ facetName: facetSection, facetUri: '' }))
  }

  const handleShowLess = (): void => {
    const currentRequest = `call${page}`
    if (facetValues.requests[currentRequest]) {
      delete facetValues.requests[currentRequest]
    }
    setFacets(facetValues)
    setPage(page - 1)
  }

  const list = (): JSX.Element[] => {
    const facetListCombined: Array<IOrderedItems> = []

    Object.keys(facetValues.requests).map((key) => {
      facetValues.requests[key].map((facet) => {
        if (facet.value !== null) {
          facetListCombined.push(facet)
        }
        return null
      })
      return null
    })

    // Filter types to only show predefined labels + 'less...'
    if (facetSection === 'Type' || facetSection === 'itemClassificationLabel') {
      let allowedSet = AllowedTypeLabels
      
      const filteredList: Array<IOrderedItems> = []
      const allowedKeys: Set<string> = new Set()
      
      for (const facet of facetListCombined) {
        const value = String(facet.value)
        if (allowedSet.includes(value)) {
          filteredList.push(facet)
          allowedKeys.add(value)
        }
      }
      
      const hasLess = allowedKeys.size === AllowedTypeLabels.length - 1
      if (hasLess && filteredList.length > 0) {
        const lessItem: IOrderedItems = {
          value: 'less...',
          id: '' as IOrderedItems['id'],
          type: 'NonMutable' as IOrderedItems['type'],
          totalItems: facetListCombined.length - filteredList.length,
        }
        filteredList.push(lessItem)
      }

      return filteredList.map((facet) => (
        <React.Fragment key={facet.value}>
          <Checkbox
            criteria={criteria}
            facet={facet}
            facetSection={facetSection}
            selectedFacets={selectedFacets}
            facetQuery={facetQuery}
            scope={scope}
          />
        </React.Fragment>
      ))
    }

    return facetListCombined.map((facet) => (
      <React.Fragment key={facet.value}>
        <Checkbox
          criteria={criteria}
          facet={facet}
          facetSection={facetSection}
          selectedFacets={selectedFacets}
          facetQuery={facetQuery}
          scope={scope}
        />
      </React.Fragment>
    ))
  }

  return (
    <React.Fragment>
      <form>
        {list()}
        {page !== lastPage && (
          <button
            type="button"
            className="btn btn-link show-more"
            onClick={() => handleShowMore()}
          >
            Show More
          </button>
        )}
        {page !== 1 && (
          <button
            type="button"
            className="btn btn-link show-less"
            onClick={() => handleShowLess()}
          >
            Show Less
          </button>
        )}
      </form>
    </React.Fragment>
  )
}

export default Checklist
