import { describe, expect, it } from 'vitest'

import { displayTitle } from '../../../../lib/util/displayTitle'

describe('displayTitle', () => {
  const schuurTitle =
    'Schuur in de duinen. In een duinlandschap ligt een schuur aan een weg. Op de weg en bij de schuur bevinden zich verschillende figuren. Zesde prent uit een genummerde serie van twaalf landschappen.'

  it('returns short titles unchanged', () => {
    expect(displayTitle('Portret van Johan de Witt')).toBe(
      'Portret van Johan de Witt',
    )
  })

  it('returns titles at the threshold unchanged', () => {
    const title = 'a'.repeat(100)
    expect(displayTitle(title)).toBe(title)
  })

  it('cuts a very long title at the first sentence', () => {
    expect(displayTitle(schuurTitle)).toBe('Schuur in de duinen.')
  })

  it('cuts the NHA Appeldorn example at the first sentence', () => {
    expect(
      displayTitle(
        'Gezicht in het dorp Appeldorn, 1746. Prent uit een 100-delige serie met gezichten op dorpen en steden te Kleef. Ets door door Paulus van Liender naar ontwerptekening van Jan de Beijer; gesigneerd en gedateerd',
      ),
    ).toBe('Gezicht in het dorp Appeldorn, 1746.')
  })

  it('skips dots inside short abbreviations such as "St."', () => {
    expect(
      displayTitle(
        'Prent van de St. Janskerk te Gouda, vervaardigd in de achttiende eeuw door een plaatselijke graveur en uitgegeven door de kerk zelf als aandenken aan de restauratie van de toren. Tweede zin.',
      ),
    ).toBe(
      'Prent van de St. Janskerk te Gouda, vervaardigd in de achttiende eeuw door een plaatselijke graveur en uitgegeven door de kerk zelf als aandenken aan de restauratie van de toren.',
    )
  })

  it('skips dots inside short numbered abbreviations such as "Nr. 3."', () => {
    expect(
      displayTitle(
        'Nr. 3. Landschap met boerderij en wat wolkenluchten in de verte boven het geheel van dit tafereel. Tweede zin over de prent.',
      ),
    ).toBe(
      'Nr. 3. Landschap met boerderij en wat wolkenluchten in de verte boven het geheel van dit tafereel.',
    )
  })

  it('hard-cuts a very long title without a sentence boundary', () => {
    const noDots = 'b'.repeat(250)
    expect(displayTitle(noDots)).toBe(`${'b'.repeat(200)}...`)
  })

  it('keeps a very long title without boundary when maxChars is 0', () => {
    const noDots = 'b'.repeat(250)
    expect(displayTitle(noDots, 0)).toBe(noDots)
  })

  it('handles null and empty titles', () => {
    expect(displayTitle(null)).toBe('')
    expect(displayTitle(undefined)).toBe('')
    expect(displayTitle('   ')).toBe('')
  })
})
