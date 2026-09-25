import React from 'react'
import { Col, Container } from 'react-bootstrap'
import { Link } from 'react-router-dom'

import StyledFooter from '../../styles/features/common/Footer'
import { pushClientEvent } from '../../lib/pushClientEvent'
import i18n from '../../i18n'

import ExternalLink from './ExternalLink'
import FeedbackButton from './FeedbackButton'
import InternalLink from './InternalLink'

const Footer: React.FC = () => (
  <StyledFooter>
    <Container fluid className="px-0">
      <footer
        className="row d-flex flex-wrap align-items-center justify-content-between h-100"
        data-testid="lux-footer"
      >
        <Col xs={12} sm={6} className="lux-footer-yale-col d-flex">
          <Link
            id="lux-footer-yale"
            to="/"
            onClick={() =>
              pushClientEvent('Internal Link', 'Selected', 'Internal NLUX')
            }
          >
            NLUX
          </Link>
        </Col>
        <Col xs={12} sm={6} className="d-flex" id="lux-footer-nav-items-col">
          <ul className="nav" id="lux-footer-nav-items">
            <li className="nav-item">
              <FeedbackButton linkName={i18n.t('footer.contact')} />
            </li>
            <li className="nav-item">
              <InternalLink
                uri="/content/terms-of-use"
                name={i18n.t('footer.termsOfUse')}
                linkCategory="Terms of Use"
              />
            </li>
            <li className="nav-item">
              <ExternalLink
                url="https://usability.yale.edu/web-accessibility/accessibility-yale"
                name={i18n.t('footer.accessibility')}
              />
            </li>
            <li className="nav-item">
              <ExternalLink
                url="https://privacy.yale.edu/resources/privacy-statement"
                name={i18n.t('footer.privacy')}
              />
            </li>
          </ul>
        </Col>
      </footer>
    </Container>
  </StyledFooter>
)

export default Footer
