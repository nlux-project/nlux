import { AllowedTypeLabels } from './facetsSlice'

export function filterSelectedTypes(
  facetList: Array<{ value: string; totalItems: number }> | null,
): Array<{ value: string; totalItems: number }> {
  if (!facetList) {
    return []
  }

  const allowedSet = new Set(AllowedTypeLabels)
  const result: Array<{ value: string; totalItems: number }> = []

  for (const item of facetList) {
    const value = String(item.value)
    if (allowedSet.has(value)) {
      result.push(item)
    }
  }

  const sortedResult = [...result].sort((a, b) => {
    if (a.value !== b.value) {
      return String(a.value).localeCompare(String(b.value), 'nl')
    }
    return b.totalItems - a.totalItems
  })

  // If all predefined labels are present and there are other items, include 'less...'
  const hasAllPredefined = AllowedTypeLabels.every((label: AllowedTypeLabelsType) =>
    result.some((item) => item.value === label)
  )

  const otherItems = result.filter((item) => !allowedSet.has(item.value))
  if (hasAllPredefined && otherItems.length > 0) {
    const maxOtherItems = otherItems[0]
    sortedResult.push({
      value: 'less...',
      totalItems: maxOtherItems.totalItems,
    })
  }

  return sortedResult
}