import React, { useState } from 'react'

import { displayTitle } from '../util/displayTitle'

const MAX_SHORT_LENGTH = 100

export function shortenIfNeeded(name: string): string {
  if (name.length > MAX_SHORT_LENGTH) {
    return `${name.substring(0, MAX_SHORT_LENGTH)}...`
  }
  return name
}

export function useResizableName(name: string): {
  displayName: string
  isNameLong: boolean
  showLongName: boolean
  setShowLongName: React.Dispatch<React.SetStateAction<boolean>>
} {
  const isNameLong = name.length > MAX_SHORT_LENGTH
  const [showLongName, setShowLongName] = useState(false)
  // The collapsed display cuts very long names at the first sentence
  // ("Schuur in de duinen."); names without a sentence boundary keep the
  // hard cut at MAX_SHORT_LENGTH as a safety net.
  const displayName = showLongName ? name : displayTitle(name, MAX_SHORT_LENGTH)

  return { displayName, isNameLong, showLongName, setShowLongName }
}
