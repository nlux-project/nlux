import React, { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import styled from 'styled-components'

import theme from '../../styles/theme'
import i18n from '../../i18n'
import config from '../../config/config'
import { useGetItemQuery, useSearchQuery } from '../../redux/api/ml_api'
import { forceArray, stripYaleIdPrefix } from '../../lib/parse/data/helper'
import EntityParser from '../../lib/parse/data/EntityParser'
import ObjectParser from '../../lib/parse/data/ObjectParser'
import { pushClientEvent } from '../../lib/pushClientEvent'
import { displayTitle } from '../../lib/util/displayTitle'
import { IOrderedItems } from '../../types/ISearchResults'

/* eslint-disable @typescript-eslint/no-explicit-any */

const Section = styled.section`
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 24px 44px;
`

const SectionTitle = styled.h2`
  font-size: 22px;
  font-weight: ${theme.font.weight.semiBold};
  margin-bottom: 18px;
`

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px;
`

const Card = styled(Link)`
  display: flex;
  flex-direction: column;
  background-color: ${theme.color.white};
  border: 1px solid ${theme.color.borderShadow};
  border-radius: 12px;
  overflow: hidden;
  text-decoration: none;
  color: ${theme.color.black};

  &:hover {
    border-color: ${theme.color.primary.blue};
    box-shadow: 0 4px 14px rgb(0 0 0 / 8%);
    text-decoration: none;
  }
`

const Thumb = styled.div`
  aspect-ratio: 4 / 3;
  background-color: ${theme.color.lightBabyBlue};
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
`

const ThumbImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: cover;
`

const CardBody = styled.div`
  padding: 12px 14px 14px;
`

const TypeBadge = styled.span`
  display: inline-block;
  font-size: 11.5px;
  font-weight: ${theme.font.weight.medium};
  color: ${theme.color.primary.blue};
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 6px;
`

const CardTitle = styled.h3`
  font-size: 15px;
  font-weight: ${theme.font.weight.medium};
  line-height: 1.35;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`

const Institution = styled.p`
  font-size: 13px;
  color: ${theme.color.gray};
  margin-bottom: 2px;
`

const Year = styled.p`
  font-size: 12.5px;
  color: ${theme.color.gray};
  margin: 0;
`

/**
 * Finds the first _label in a (nested) classified_as structure.
 */
const getTypeLabel = (data: any): string => {
  const walk = (node: any): string => {
    if (Array.isArray(node)) {
      for (const child of node) {
        const label = walk(child)
        if (label) {
          return label
        }
      }
      return ''
    }
    if (typeof node === 'object' && node !== null) {
      if (typeof node._label === 'string' && node._label !== '') {
        return node._label
      }
      return walk(node.classified_as)
    }
    return ''
  }
  return walk(data?.classified_as)
}

/**
 * Turns a raw timespan string into a compact year display, keeping
 * human-readable values such as "ca. 1650" or "Middeleeuwen" as they are.
 */
const formatYear = (date: string | null): string => {
  if (date === null || date === '') {
    return ''
  }
  const isoMatch = date.match(/^(\d{4})/)
  if (isoMatch && date.length > 4) {
    return isoMatch[1]
  }
  return date
}

interface IHighlightsCardProps {
  uri: string
}

const HighlightsCard: React.FC<IHighlightsCardProps> = ({ uri }) => {
  const [imageFailed, setImageFailed] = useState(false)

  const { data, isSuccess } = useGetItemQuery({
    uri: stripYaleIdPrefix(uri),
    profile: 'results',
  })

  if (!isSuccess || !data) {
    return null
  }

  const raw = data as any
  const entity = new EntityParser(data)
  const images = entity.getImages()
  const imageUrl =
    images.length > 0 && images[0].imageUrls.length > 0
      ? images[0].imageUrls[0]
      : ''
  if (imageUrl === '' || imageFailed) {
    return null
  }

  const primaryName =
    entity.getPrimaryName(config.aat.langen) || data._label || ''
  const title = displayTitle(primaryName)
  const typeLabel = getTypeLabel(raw)
  const institution = forceArray(raw.current_owner)[0]?._label ?? ''
  const year = formatYear(new ObjectParser(raw).getDateFromProductionEvent())
  const recordId = data.id ?? uri
  const link = `/view/${stripYaleIdPrefix(recordId)}`

  return (
    <Card
      to={link}
      data-testid="highlights-card"
      onClick={() => {
        pushClientEvent('Highlights', 'Selected', 'Landing Page Highlight')
      }}
    >
      <Thumb>
        <ThumbImage
          src={imageUrl}
          alt={primaryName}
          loading="lazy"
          onError={() => setImageFailed(true)}
        />
      </Thumb>
      <CardBody>
        {typeLabel !== '' && <TypeBadge>{typeLabel}</TypeBadge>}
        <CardTitle>{title}</CardTitle>
        {institution !== '' && <Institution>{institution}</Institution>}
        {year !== '' && <Year>{year}</Year>}
      </CardBody>
    </Card>
  )
}

const HIGHLIGHT_COUNT = 4

/**
 * A title qualifies for the highlights grid: archival records sometimes
 * carry purely numeric titles such as "16", which are meaningless as a
 * highlight.
 */
const isHighlightTitle = (title: unknown): boolean => {
  if (typeof title !== 'string') {
    return false
  }
  const trimmed = title.trim()
  return trimmed.length >= 4 && !/^\d+([.,]\d+)?$/.test(trimmed)
}

/**
 * The "Uitgelicht" section on the landing page: records with images from the
 * search API (mirrors the Collectie NH Mockup B highlights grid).
 */
const HighlightsSection: React.FC = () => {
  const { data, isSuccess } = useSearchQuery(
    {
      q: JSON.stringify({ hasDigitalImage: 1 }),
      tab: 'objects',
      page: 1,
      facets: {},
    },
    // A fresh set of highlights on every landing page visit
    { refetchOnMountOrArgChange: true },
  )

  const highlights = useMemo(() => {
    if (!isSuccess || !data) {
      return []
    }
    const orderedItems: Array<IOrderedItems & { label?: string }> =
      data.orderedItems ?? []
    const titled = orderedItems.filter((item) =>
      isHighlightTitle(item.label ?? ''),
    )
    const shuffled = [...titled].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, HIGHLIGHT_COUNT)
  }, [data, isSuccess])

  if (highlights.length === 0) {
    return null
  }

  return (
    <Section data-testid="highlights-container">
      <SectionTitle>{i18n.t('landing.highlightsTitle')}</SectionTitle>
      <Grid>
        {highlights.map((item) => (
          <HighlightsCard key={item.id} uri={item.id} />
        ))}
      </Grid>
    </Section>
  )
}

export default HighlightsSection
