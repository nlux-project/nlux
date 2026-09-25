import React from 'react'
import styled from 'styled-components'

import i18n from '../../i18n'
import close from '../../resources/images/icons/close.svg'
import search from '../../resources/images/icons/search.svg'

const StyledButton = styled.button`
  background-color: inherit;
  border-style: none;
  padding: 0.5rem 0rem;
`
const CloseImg = styled.img`
  margin: 7.5px;
  float: left;
`

const SearchImg = styled.img`
  float: left;
`

const SearchButton: React.FC<{
  displaySearch: boolean
  setIsSearchOpen: (isSearchOpen: boolean) => void
}> = ({ displaySearch, setIsSearchOpen }) => (
  <StyledButton
    type="button"
    aria-label={displaySearch ? i18n.t('search.close') : i18n.t('search.open')}
    onClick={() => setIsSearchOpen(!displaySearch)}
  >
    {displaySearch ? (
      <CloseImg alt={i18n.t('search.close')} src={close} />
    ) : (
      <SearchImg alt={i18n.t('search.open')} src={search} />
    )}
  </StyledButton>
)

export default SearchButton
