import React from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import styled from 'styled-components'

import theme from '../../styles/theme'
import i18n from '../../i18n'
import { pushClientEvent } from '../../lib/pushClientEvent'
import { getParamPrefix } from '../../lib/util/params'
import { ResultsTab } from '../../types/ResultsTab'

const SortLabel = styled.span`
  font-size: 13px;
  font-weight: ${theme.font.weight.regular};
  color: ${theme.color.gray};
`

const SortSelect = styled.select`
  margin-left: 8px;
  padding: 6px 10px;
  font-size: 13px;
  font-weight: ${theme.font.weight.medium};
  color: ${theme.color.black};
  background-color: ${theme.color.white};
  border: 1px solid ${theme.color.borderShadow};
  border-radius: 8px;
`

const SORT_OPTIONS: Array<{ value: string; labelKey: string }> = [
  { value: 'relevance', labelKey: 'results.sortRelevance' },
  { value: 'anySortName:asc', labelKey: 'results.sortNameAZ' },
  { value: 'itemProductionDate:desc', labelKey: 'results.sortNewestFirst' },
]

/**
 * Simple sort dropdown for the objects results tab: relevance, title A–Z and
 * newest first (mirrors the Collectie NH Mockup B design). Writes the `is`
 * URL parameter and resets pagination when the sort changes.
 */
const ResultsSortDropdown: React.FC = () => {
  const { pathname, search } = useLocation()
  const navigate = useNavigate()
  const { tab, subTab } = useParams<keyof ResultsTab>() as ResultsTab
  const paramPrefix = getParamPrefix(subTab ? subTab : tab)
  const sortParam = `${paramPrefix}s`
  const pageParam = `${paramPrefix}p`

  const urlParams = new URLSearchParams(search)
  const currentSort = urlParams.get(sortParam) ?? 'relevance'

  const handleSortChange = (sort: string): void => {
    pushClientEvent('Sort Dropdown', 'Selected', sort)
    const params = new URLSearchParams(search)
    if (sort === 'relevance') {
      params.delete(sortParam)
    } else {
      params.set(sortParam, sort)
    }
    params.delete(pageParam)
    navigate({
      pathname,
      search: `?${params.toString()}`,
    })
  }

  return (
    <div
      className="d-flex align-items-center"
      data-testid="results-sort-dropdown"
    >
      <SortLabel>{i18n.t('results.sortLabel')}</SortLabel>
      <SortSelect
        value={currentSort}
        onChange={(event) => handleSortChange(event.target.value)}
        aria-label={i18n.t('results.sortLabel')}
      >
        {SORT_OPTIONS.map((option) => (
          <option
            key={option.value}
            value={option.value}
            data-testid="results-sort-option"
          >
            {i18n.t(option.labelKey)}
          </option>
        ))}
      </SortSelect>
    </div>
  )
}

export default ResultsSortDropdown
