import React from 'react'
import { HashLink as Link } from 'react-router-hash-link'

import { scopeToTabTranslation } from '../../config/searchTypes'
import { IAdvancedSearchState } from '../../redux/slices/advancedSearchSlice'
import { pushClientEvent } from '../../lib/pushClientEvent'
import i18n from '../../i18n'
import { translateLabel } from '../../lib/i18n/translateLabel'
import { convertToANDQuery } from '../../lib/parse/search/queryParser'

interface ILinkParams {
  scope: string
  criteria: IAdvancedSearchState
  id: string
  title: string
  total?: number
  label?: string
}

const RelatedListSearchLink: React.FC<ILinkParams> = ({
  scope,
  criteria,
  id,
  title,
  total,
  label,
}) => {
  const tab = scopeToTabTranslation[scope]

  const linkLabel =
    total !== undefined
      ? i18n.t('related.showAllLabelResults', {
          count: total,
          label: translateLabel(label),
        })
      : i18n.t('related.showAll')

  const searchQ = convertToANDQuery(JSON.stringify(criteria))
  return (
    <Link
      to={{
        pathname: `/view/results/${tab}`,
        search: `q=${searchQ}&searchLink=true`,
      }}
      onClick={() =>
        pushClientEvent('Search Link', 'Selected', `Accordion ${title}`)
      }
      data-testid={`related-list-search-link-${id}`}
    >
      {linkLabel}
    </Link>
  )
}

export default RelatedListSearchLink
