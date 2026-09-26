import React, { useState } from 'react'
import { ErrorBoundary } from 'react-error-boundary'
import { Row, Col } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import styled from 'styled-components'

import { UnitCode } from '../../config/cms'
import { fullTextSearchUrl, quickSearches } from '../../config/institutions'
import { pickRandomUnits } from '../../lib/cms/util'
import { ErrorFallback } from '../error/ErrorFallback'
import {
  useGetFeaturedCollectionsQuery,
  useGetLandingPageQuery,
  useGetLandingPageImagesQuery,
} from '../../redux/api/cmsApi'
import { useGetStatsQuery } from '../../redux/api/ml_api'
import { StyledLandingPage } from '../../styles/features/landing/LandingPage'
import theme from '../../styles/theme'
import i18n from '../../i18n'
import SearchContainer from '../search/SearchContainer'

import FeaturedCollectionsSection from './FeaturedCollectionsSection'
import FooterBlocks from './FooterBlocksSection'
import HeroImageSection from './HeroImageSection'
import InstitutionsSection from './InstitutionsSection'
import Infographics from './InfographicsSection'
import MoreAboutLux from './MoreAboutLuxSection'

const HeroSection = styled.section`
  background: linear-gradient(150deg, #eaf3f8 0%, #f6fbfe 55%, #ffffff 100%);
  padding: 56px 24px 44px;
  text-align: center;
`

const HeroTitle = styled.h1`
  font-size: clamp(28px, 4.5vw, 44px);
  font-weight: ${theme.font.weight.light};
  letter-spacing: -0.5px;
  line-height: 1.2;
  color: ${theme.color.black};
`

const HeroSubtitle = styled.p`
  color: #5c7080;
  font-size: 17px;
  font-weight: ${theme.font.weight.regular};
  margin: 14px auto 30px;
  max-width: 640px;
`

const QuickChips = styled.div`
  margin-top: 8px;
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
`

const QuickChip = styled(Link)`
  background-color: ${theme.color.white};
  border: 1px solid ${theme.color.borderShadow};
  color: ${theme.color.primary.blue};
  padding: 7px 16px;
  border-radius: 999px;
  font-size: 13.5px;
  font-weight: ${theme.font.weight.medium};
  text-decoration: none;

  &:hover {
    background-color: ${theme.color.primary.blue};
    color: ${theme.color.white};
    text-decoration: none;
  }
`

const Landing: React.FC = () => {
  const [units, setUnits] = useState([] as UnitCode[])

  const landingPageResult = useGetLandingPageQuery()
  const imagesResult = useGetLandingPageImagesQuery()
  const featuredResult = useGetFeaturedCollectionsQuery()
  const statsResult = useGetStatsQuery()

  if (
    imagesResult.isSuccess &&
    featuredResult.isSuccess &&
    units.length === 0
  ) {
    setUnits(pickRandomUnits())
  }

  return (
    <StyledLandingPage id="landing-body" className="mx-0">
      <Col xs={12} className="px-0">
        <HeroSection data-testid="landing-hero">
          <HeroTitle>{i18n.t('landing.heroTitle')}</HeroTitle>
          <HeroSubtitle>{i18n.t('landing.heroSub')}</HeroSubtitle>
          <SearchContainer
            className=""
            bgColor="transparent"
            id="landing-page-search-container"
          />
          <QuickChips>
            {quickSearches.map((quickSearch) => (
              <QuickChip
                key={quickSearch.term}
                to={fullTextSearchUrl(quickSearch.term)}
              >
                {quickSearch.label}
              </QuickChip>
            ))}
          </QuickChips>
        </HeroSection>
        <Row id="srch-hero-container" className="mx-0">
          {imagesResult.isSuccess && units.length > 0 && (
            <ErrorBoundary FallbackComponent={ErrorFallback}>
              <Row className="d-flex row mx-0 px-0 pt-4">
                <Col className="px-0">
                  <HeroImageSection data={imagesResult.data} unit={units[0]} />
                </Col>
              </Row>
            </ErrorBoundary>
          )}
        </Row>
        {featuredResult.isSuccess && units.length > 0 && (
          <Row className="mx-0">
            <Col xs={12}>
              <ErrorBoundary FallbackComponent={ErrorFallback}>
                <FeaturedCollectionsSection
                  data={featuredResult.data}
                  units={units.slice(1)}
                />
              </ErrorBoundary>
            </Col>
          </Row>
        )}
        <InstitutionsSection />
        {landingPageResult.isSuccess && landingPageResult.data && (
          <Row className="mx-0">
            <Col xs={12}>
              <ErrorBoundary FallbackComponent={ErrorFallback}>
                <MoreAboutLux data={landingPageResult.data} />
              </ErrorBoundary>
            </Col>
          </Row>
        )}
        {statsResult.isSuccess && statsResult.data && (
          <Row className="mx-0">
            <Col xs={12}>
              <ErrorBoundary FallbackComponent={ErrorFallback}>
                <Infographics data={statsResult.data} />
              </ErrorBoundary>
            </Col>
          </Row>
        )}
        {landingPageResult.isSuccess && landingPageResult.data && (
          <Row className="mx-0">
            <Col xs={12}>
              <ErrorBoundary FallbackComponent={ErrorFallback}>
                <FooterBlocks data={landingPageResult.data} />
              </ErrorBoundary>
            </Col>
          </Row>
        )}
      </Col>
    </StyledLandingPage>
  )
}

export default Landing
