import styled from 'styled-components'

import theme from '../../theme'

const Header = styled.div`
  width: 100%;
  .navbar {
    background-color: var(--nlux-primary, ${theme.color.white}) !important;
    border-bottom: 1px solid ${theme.color.black10};
    padding: 1.25 auto;

    .container {
      width: 100%;
    }
  }

  .navbarContainer {
    justify-content: start;

    @media (min-width: ${theme.breakpoints.md}px) {
      justify-content: space-between;
    }
  }

  .navbar-brand {
    font-family: YaleDesign, serif;
    font-weight: 400;
    color: var(--nlux-font, ${theme.color.black});
    white-space: pre-wrap;
    order: 2;

    @media (min-width: ${theme.breakpoints.md}px) {
      order: 1;
    }
  }

  #nav-links a {
    color: var(--nlux-font, ${theme.color.black});
    font-weight: ${theme.font.weight.medium};

    &.navDropdownItem {
      color: ${theme.color.trueBlack};

      &:active {
        color: ${theme.color.white};
        background-color: ${theme.color.primary.blue};
      }
    }
  }

  .navbar-light .navbar-toggler,
  .navbar-dark .navbar-toggler {
    color: var(--nlux-font, ${theme.color.black});
    border: none;
    font-weight: ${theme.font.weight.medium};
    order: 1;

    @media (min-width: ${theme.breakpoints.lg}px) {
      float: right;
      padding: 0;
    }

    @media (min-width: ${theme.breakpoints.md}px) {
      order: 2;
    }
  }

  .navbar-collapse {
    order: 3;
  }

  @media (min-width: ${theme.breakpoints.sm}px) {
    &.navbar-collapse {
      display: block;
      flex-basis: auto;
    }

    .navbar-brand {
      font-size: 2em;
    }
  }
`

export default Header
