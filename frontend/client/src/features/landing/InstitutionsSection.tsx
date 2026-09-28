import React from 'react'
import { Link } from 'react-router-dom'
import styled from 'styled-components'

import { institutions, institutionSearchUrl } from '../../config/institutions'
import { useGetSearchEstimateQuery } from '../../redux/api/ml_api'
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

const InstitutionName = styled.span`
  display: block;
`

const InstitutionCount = styled.span`
  display: block;
  color: ${theme.color.gray};
  font-size: 12.5px;
  font-weight: ${theme.font.weight.light};
  margin-top: 2px;
`

interface IInstitutionCardProps {
  name: string
  searchTerm: string
}

const InstitutionCardItem: React.FC<IInstitutionCardProps> = ({
  name,
  searchTerm,
}) => {
  const { data: totalItems } = useGetSearchEstimateQuery({
    scope: 'item',
    q: searchTerm,
  })

  return (
    <InstitutionCard
      to={institutionSearchUrl(searchTerm)}
      data-testid={`institution-card-${name}`}
    >
      <InstitutionName>{name}</InstitutionName>
      {totalItems !== undefined && (
        <InstitutionCount data-testid={`institution-count-${name}`}>
          {i18n.t('landing.institutionObjects', { count: totalItems })}
        </InstitutionCount>
      )}
    </InstitutionCard>
  )
}

const InstitutionsSection: React.FC = () => (
  <Section data-testid="institutions-container">
    <SectionTitle>{i18n.t('landing.institutionsTitle')}</SectionTitle>
    <Grid>
      {institutions.map((institution) => (
        <InstitutionCardItem
          key={institution.name}
          name={institution.name}
          searchTerm={institution.searchTerm}
        />
      ))}
    </Grid>
  </Section>
)

export default InstitutionsSection
