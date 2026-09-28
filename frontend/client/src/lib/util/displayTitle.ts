/**
 * Long archival titles dominate list snippets and highlight cards. When a
 * title exceeds TITLE_LONG_THRESHOLD characters and contains a
 * sentence-ending '.', only the first sentence is displayed — mirrors the
 * carousel's displayTitle() (caroussel/frontend/src/components/Carousel.js).
 * Dots that belong to an abbreviation are skipped: heads shorter than
 * TITLE_MIN_HEAD ("Nr. 3.") and heads ending in a short capitalized token
 * ("Prent van de St.") are not treated as a sentence boundary.
 */
const TITLE_LONG_THRESHOLD = 100
const TITLE_MIN_HEAD = 10
const ABBREV_WORD_MAX = 3

const isAbbreviationDot = (head: string): boolean => {
  if (head.length < TITLE_MIN_HEAD) {
    return true
  }
  const word = head.slice(head.lastIndexOf(' ') + 1)
  return word.length <= ABBREV_WORD_MAX && /^[A-Z]/.test(word)
}

/**
 * Returns the display form of a title: the full title when it is short
 * enough, otherwise the first sentence ("Schuur in de duinen."). When the
 * title is very long but has no sentence-ending '.', it is hard-cut at
 * maxChars with an ellipsis (safety net for pathological titles).
 */
export const displayTitle = (
  title: string | null | undefined,
  maxChars = 200,
): string => {
  const full = (title ?? '').trim()
  if (full.length <= TITLE_LONG_THRESHOLD) {
    return full
  }
  let from = 0
  while (from < full.length) {
    const dot = full.indexOf('.', from)
    if (dot === -1) {
      break
    }
    if (!isAbbreviationDot(full.slice(0, dot))) {
      return `${full.slice(0, dot).trim()}.`
    }
    from = dot + 1
  }
  if (maxChars > 0 && full.length > maxChars) {
    return `${full.slice(0, maxChars)}...`
  }
  return full
}
