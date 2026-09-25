import React from 'react'
import sanitizeHtml from 'sanitize-html'

import { IAiResearch } from '../../types/IContentWithLanguage'

interface IProps {
  research: IAiResearch | null
}

const AiResearch: React.FC<IProps> = ({ research }) => {
  if (research === null) {
    return null
  }

  const html = research.htmlContent || research.content

  return (
    <div className="aiResearchCard" data-testid="ai-research-card">
      <h3>AI Research</h3>
      <div
        data-testid="ai-research-content"
        dangerouslySetInnerHTML={{
          __html: sanitizeHtml(html),
        }}
      />
    </div>
  )
}

export default AiResearch
