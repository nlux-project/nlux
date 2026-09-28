import { describe, expect, it } from 'vitest'

import { displayYear } from '../../../../lib/util/displayYear'

describe('displayYear', () => {
  it('reduces a full ISO timestamp to the bare year', () => {
    expect(displayYear('1620-01-01T00:00:00')).toEqual('1620')
  })

  it('reduces an ISO date with timezone to the bare year', () => {
    expect(displayYear('1780-01-01T00:00:00Z')).toEqual('1780')
    expect(displayYear('1983-12-31T23:59:59+01:00')).toEqual('1983')
  })

  it('reduces a plain ISO date to the bare year', () => {
    expect(displayYear('1620-01-01')).toEqual('1620')
  })

  it('leaves a bare year unchanged', () => {
    expect(displayYear('1620')).toEqual('1620')
  })

  it('leaves a date range unchanged', () => {
    expect(displayYear('1988-01-01 - 1988-07-24')).toEqual(
      '1988-01-01 - 1988-07-24',
    )
  })

  it('leaves free text unchanged', () => {
    expect(displayYear('ca. 1620')).toEqual('ca. 1620')
    expect(displayYear('17e eeuw')).toEqual('17e eeuw')
  })

  it('keeps a negative (BCE) year intact when reducing', () => {
    expect(displayYear('-0500-01-01T00:00:00')).toEqual('-0500')
  })
})
