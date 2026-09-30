import React from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import styled from 'styled-components'

import theme from '../../styles/theme'
import i18n from '../../i18n'
import { useGetFacetsSearchQuery } from '../../redux/api/ml_api'
import { pushClientEvent } from '../../lib/pushClientEvent'
import { getParamPrefix } from '../../lib/util/params'
import { ResultsTab } from '../../types/ResultsTab'
import { IOrderedItems } from '../../types/ISearchResults'

/* eslint-disable @typescript-eslint/no-explicit-any */

interface IRefineSelection {
  owners: string[]
  types: string[]
  period: string
}

const EMPTY_SELECTION: IRefineSelection = { owners: [], types: [], period: '' }

const PERIOD_RANGES: Record<string, Record<string, number>> = {
  pre1600: { end: 1600 },
  '1600-1800': { begin: 1600, end: 1800 },
  '1800-1950': { begin: 1800, end: 1950 },
  post1950: { begin: 1950 },
}

const PERIOD_LABEL_KEYS: Record<string, string> = {
  '': 'refine.allPeriods',
  pre1600: 'refine.before1600',
  '1600-1800': 'refine.period1600to1800',
  '1800-1950': 'refine.period1800to1950',
  post1950: 'refine.after1950',
}

const PERIODS = ['', 'pre1600', '1600-1800', '1800-1950', 'post1950']

/**
 * Flattens an AND/OR criteria tree into its leaf criteria.
 */
const collectLeaves = (
  node: any,
  leaves: Array<Record<string, any>> = [],
): Array<Record<string, any>> => {
  if (Array.isArray(node)) {
    node.forEach((child) => collectLeaves(child, leaves))
  } else if (typeof node === 'object' && node !== null) {
    if ('AND' in node || 'OR' in node) {
      collectLeaves(node.AND ?? node.OR, leaves)
    } else {
      leaves.push(node)
    }
  }
  return leaves
}

/**
 * Reads the current facet criteria from the `if` URL parameter.
 */
const extractSelection = (facetCriteria: any): IRefineSelection => {
  const selection: IRefineSelection = { owners: [], types: [], period: '' }
  for (const leaf of collectLeaves(facetCriteria)) {
    if (typeof leaf.currentOwnerLabel === 'string') {
      selection.owners.push(leaf.currentOwnerLabel)
    } else if (typeof leaf.classificationLabel === 'string') {
      selection.types.push(leaf.classificationLabel)
    } else if (leaf.productionDateRange) {
      const { begin, end } = leaf.productionDateRange
      selection.period =
        Object.keys(PERIOD_RANGES).find(
          (key) =>
            PERIOD_RANGES[key].begin === begin &&
            PERIOD_RANGES[key].end === end,
        ) ?? ''
    }
  }
  return selection
}

/**
 * Builds the facet criteria (`if` URL parameter) for the given selection.
 */
const buildFacetQuery = (selection: IRefineSelection): string | null => {
  const groups: any[] = []
  if (selection.owners.length > 0) {
    groups.push(
      selection.owners.length === 1
        ? { currentOwnerLabel: selection.owners[0] }
        : {
            OR: selection.owners.map((owner) => ({ currentOwnerLabel: owner })),
          },
    )
  }

  // Build the filter groups from the selection
  if (selection.types.length > 0) {
    groups.push(
      selection.types.length === 1
        ? { classificationLabel: selection.types[0] }
        : {
            OR: selection.types.map((type) => ({
              classificationLabel: type,
            })),
          },
    )
  }

  if (selection.period !== '') {
    groups.push({ productionDateRange: PERIOD_RANGES[selection.period] })
  }

  if (groups.length === 0) {
    return null
  }
  return JSON.stringify(groups.length === 1 ? groups[0] : { AND: groups })
}

const Panel = styled.aside`
  padding: 18px 18px 22px;
`

const PanelTitle = styled.h3`
  font-size: 16px;
  font-weight: ${theme.font.weight.semiBold};
  color: ${theme.color.black};
  margin-bottom: 14px;
`

const GroupTitle = styled.h4`
  font-size: 13px;
  font-weight: ${theme.font.weight.semiBold};
  color: ${theme.color.gray};
  margin: 14px 0 6px;
`

const OptionList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
`

const OptionLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13.5px;
  font-weight: ${theme.font.weight.regular};
  color: ${theme.color.black};
  cursor: pointer;
  word-break: break-word;

  input {
    accent-color: ${theme.color.primary.blue};
    flex-shrink: 0;
  }
`

const Count = styled.span`
  color: ${theme.color.gray};
  font-size: 12px;
`

const ClearButton = styled.button`
  margin-top: 18px;
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: ${theme.font.weight.medium};
  color: ${theme.color.primary.blue};
  background-color: transparent;
  border: 1px solid ${theme.color.borderShadow};
  border-radius: 8px;

  &:hover {
    background-color: ${theme.color.lightBabyBlue};
  }
`

interface IRefinePanelProps {
  facetName: string
  labelKey: string
  selectedValues: string[]
  combinedQuery: string
  onToggle: (value: string, checked: boolean) => void
}

const FacetCheckboxGroup: React.FC<IRefinePanelProps> = ({
  facetName,
  labelKey,
  selectedValues,
  combinedQuery,
  onToggle,
}) => {
  const { tab } = useParams<keyof ResultsTab>() as ResultsTab

  const { data, isSuccess, isLoading } = useGetFacetsSearchQuery({
    q: combinedQuery,
    facets: {},
    facetNames: facetName,
    tab,
    page: 1,
  })

  if (isLoading) {
    return null
  }

  if (!isSuccess || !data) {
    return null
  }

  const { orderedItems } = data
  const values: Array<IOrderedItems> = (orderedItems ?? [])
    .filter((item: IOrderedItems) => item.value !== null)
    // Filter to only show main types
    .filter((item: IOrderedItems) => {
      const value = String(item.value)
      const mainTypes = [
        'Prenten',
        'Tekeningen', 
        'Schilderijen',
        'Foto\'s',
      ]
      return mainTypes.includes(value)
    })
    .sort((a: IOrderedItems, b: IOrderedItems) => {
      if ((b.totalItems ?? 0) !== (a.totalItems ?? 0)) {
        return (b.totalItems ?? 0) - (a.totalItems ?? 0)
      }
      return String(a.value).localeCompare(String(b.value), 'nl')
    })

  if (values.length === 0) {
    return null
  }

  return (
    <div data-testid={`refine-group-${facetName}`}>
      <GroupTitle>{i18n.t(labelKey)}</GroupTitle>
      <OptionList>
        {displayValues.map((item: IOrderedItems) => {
          const value = String(item.value)
          const checked = selectedValues.includes(value)
          
          return (
            <OptionLabel
              key={value}
              data-testid={`refine-option-${facetName}-${value}`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={(event) => onToggle(value, event.target.checked)}
              />
              {value}
              <Count>{item.totalItems}</Count>
            </OptionLabel>
          )
        })}
      </OptionList>
    </div>
  )
}

/**
 * The "Verfijn resultaten" sidebar for the objects results tab: institution
 * and type checkboxes backed by the facets API, period radio buckets and a
 * reset button (mirrors the Collectie NH Mockup B design).
 */
const RefinePanel: React.FC = () => {
  const { pathname, search } = useLocation()
  const navigate = useNavigate()
  const { tab, subTab } = useParams<keyof ResultsTab>() as ResultsTab
  const paramPrefix = getParamPrefix(subTab ? subTab : tab)
  const facetParam = `${paramPrefix}f`
  const pageParam = `${paramPrefix}p`

  const urlParams = new URLSearchParams(search)
  const queryString = urlParams.get('q') || ''
  const facetSearchString = urlParams.get(facetParam)

  if (queryString === '' || !queryString.startsWith('{')) {
    return null
  }

  let baseCriteria: Record<string, any>
  try {
    baseCriteria = JSON.parse(queryString)
  } catch {
    return null
  }

  let selection = EMPTY_SELECTION
  if (facetSearchString) {
    try {
      selection = extractSelection(JSON.parse(facetSearchString))
    } catch {
      selection = EMPTY_SELECTION
    }
  }

  const navigateWithSelection = (newSelection: IRefineSelection): void => {
    const params = new URLSearchParams(search)
    const facetQuery = buildFacetQuery(newSelection)
    if (facetQuery) {
      params.set(facetParam, facetQuery)
    } else {
      params.delete(facetParam)
    }
    params.delete(pageParam)
    navigate({
      pathname,
      search: `?${params.toString()}`,
    })
  }

  const toggleValue = (
    values: string[],
    value: string,
    checked: boolean,
  ): string[] =>
    checked ? [...values, value] : values.filter((item) => item !== value)

  const handleToggleOwner = (value: string, checked: boolean): void => {
    pushClientEvent('Refine Panel', 'Selected', `Institution ${value}`)
    navigateWithSelection({
      ...selection,
      owners: toggleValue(selection.owners, value, checked),
    })
  }

  const handleToggleType = (value: string, checked: boolean): void => {
    pushClientEvent('Refine Panel', 'Selected', `Type ${value}`)
    navigateWithSelection({
      ...selection,
      types: toggleValue(selection.types, value, checked),
    })
  }

  const handleSelectPeriod = (period: string): void => {
    pushClientEvent('Refine Panel', 'Selected', `Period ${period || 'all'}`)
    navigateWithSelection({ ...selection, period })
  }

  const handleClear = (): void => {
    pushClientEvent('Refine Panel', 'Clicked', 'Clear filters')
    navigateWithSelection(EMPTY_SELECTION)
  }

  const hasSelection =
    selection.owners.length > 0 ||
    selection.types.length > 0 ||
    selection.period !== ''

  // Counts for a group must not include that group's own selections so
  // that switching between values stays possible.
  const combinedQueryFor = (exclude: 'owners' | 'types'): string => {
    const excluded: IRefineSelection = {
      owners: exclude === 'owners' ? [] : selection.owners,
      types: exclude === 'types' ? [] : selection.types,
      period: selection.period,
    }
    const facetQuery = buildFacetQuery(excluded)
    if (!facetQuery) {
      return queryString
    }
    return JSON.stringify({
      AND: [baseCriteria, JSON.parse(facetQuery)],
    })
  }

  return (
    <Panel data-testid="refine-panel">
      <PanelTitle>{i18n.t('refine.title')}</PanelTitle>
      <FacetCheckboxGroup
        facetName="itemCurrentOwnerLabel"
        labelKey="refine.institution"
        selectedValues={selection.owners}
        combinedQuery={combinedQueryFor('owners')}
        onToggle={handleToggleOwner}
      />
      <FacetCheckboxGroup
        facetName="itemClassificationLabel"
        labelKey="refine.type"
        selectedValues={selection.types}
        combinedQuery={combinedQueryFor('types')}
        onToggle={handleToggleType}
      />
      <div data-testid="refine-group-period">
        <GroupTitle>{i18n.t('refine.period')}</GroupTitle>
        <OptionList>
          {PERIODS.map((period) => (
            <OptionLabel key={period || 'all'}>
              <input
                type="radio"
                name="refine-period"
                value={period}
                checked={selection.period === period}
                onChange={() => handleSelectPeriod(period)}
              />
              {i18n.t(PERIOD_LABEL_KEYS[period])}
            </OptionLabel>
          ))}
        </OptionList>
      </div>
      {hasSelection && (
        <ClearButton
          type="button"
          onClick={handleClear}
          data-testid="refine-clear-button"
        >
          {i18n.t('refine.clear')}
        </ClearButton>
      )}
    </Panel>
  )
}

export default RefinePanel
