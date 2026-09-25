import i18n from '../../i18n'

export function translateLabel(label?: string): string | undefined {
  if (label === undefined || label === '') {
    return label
  }

  return i18n.t(`labels.${label}`, { defaultValue: label })
}
