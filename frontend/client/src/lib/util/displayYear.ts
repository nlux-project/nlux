/**
 * Returns the year component of an event date for display purposes.
 *
 * Full ISO date/timestamp strings (e.g. `1620-01-01T00:00:00` or
 * `1620-01-01`) are reduced to the bare year (`1620`). Anything else
 * (already bare years, ranges such as `1988-01-01 - 1988-07-24`, or
 * free text like `ca. 1620`) is returned unchanged.
 *
 * @param {string} date the date string to be displayed
 * @returns {string}
 */
const ISO_DATE = /^(-?\d{4})(-\d{2}(-\d{2})?)?(T[\d:.]+(Z|[+-]\d{2}:?\d{2})?)?$/

export const displayYear = (date: string): string => {
  const match = date.trim().match(ISO_DATE)
  return match !== null ? match[1] : date
}
