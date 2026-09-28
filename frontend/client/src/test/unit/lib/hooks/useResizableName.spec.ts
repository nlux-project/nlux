import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import {
  shortenIfNeeded,
  useResizableName,
} from '../../../../lib/hooks/useResizableName'

const schuurTitle =
  'Schuur in de duinen. In een duinlandschap ligt een schuur aan een weg. Op de weg en bij de schuur bevinden zich verschillende figuren. Zesde prent uit een genummerde serie van twaalf landschappen.'

describe('useResizbleName exported functions', () => {
  describe('shortenIfNeeded', () => {
    it('returns shortened array', () => {
      const longTitle =
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'
      const shortTitle =
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore ...'
      expect(shortenIfNeeded(longTitle)).toEqual(shortTitle)
    })
  })

  describe('useResizableName', () => {
    it('shows the first sentence for very long names', () => {
      const { result } = renderHook(() => useResizableName(schuurTitle))
      expect(result.current.displayName).toBe('Schuur in de duinen.')
      expect(result.current.isNameLong).toBe(true)
    })

    it('shows the full name after toggling', () => {
      const { result } = renderHook(() => useResizableName(schuurTitle))
      act(() => result.current.setShowLongName(true))
      expect(result.current.displayName).toBe(schuurTitle)
    })

    it('hard-cuts long names without a sentence boundary', () => {
      const noDots = 'b'.repeat(250)
      const { result } = renderHook(() => useResizableName(noDots))
      expect(result.current.displayName).toBe(`${'b'.repeat(100)}...`)
    })

    it('returns short names unchanged', () => {
      const { result } = renderHook(() =>
        useResizableName('Portret van Johan de Witt'),
      )
      expect(result.current.displayName).toBe('Portret van Johan de Witt')
      expect(result.current.isNameLong).toBe(false)
    })
  })
})
