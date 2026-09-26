import React from 'react'
import { Link } from 'react-router-dom'
import styled from 'styled-components'

import { institutions, institutionSearchUrl } from '../../config/institutions'
import i18n from '../../i18n'
import theme from '../../styles/theme'

const Section = styled.section`
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 24px 40px;
`

const SectionTitle = styled.h2`
  font-size: 22px;
  font-weight: ${theme.font.weight.semiBold};
  margin-bottom: 18px;
`

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 12px;
`

const InstitutionCard = styled(Link)`
  display: block;
  background-color: ${theme.color.white};
  border: 1px solid ${theme.color.borderShadow};
  border-radius: 12px;
  padding: 14px 16px;
  color: ${theme.color.black};
  font-weight: ${theme.font.weight.medium};
  font-size: 14.5px;
  text-decoration: none;

  &:hover {
    border-color: ${theme.color.primary.blue};
    color: ${theme.color.primary.blue};
    text-decoration: none;
  }
`

const InstitutionsSection: React.FC = () => (
  <Section data-testid="institutions-container">
    <SectionTitle>{i18n.t('landing.institutionsTitle')}</SectionTitle>
    <Grid>
      {institutions.map((institution) => (
        <InstitutionCard
          key={institution.name}
          to={institutionSearchUrl(institution.searchTerm)}
          data-testid={`institution-card-${institution.name}`}
        >
          {institution.name}
        </InstitutionCard>
      ))}
    </Grid>
  </Section>
)

export default InstitutionsSection
