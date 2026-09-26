import { createInstance } from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import nl from './locales/nl.json'

// Collectie NH ships Dutch-only for now. English is fully prepared
// (resources + strings below) — switching later only requires exposing
// a language toggle and changing `lng`.
const DEFAULT_LANGUAGE = 'nl'

const i18n = createInstance()

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    nl: { translation: nl },
  },
  lng: DEFAULT_LANGUAGE,
  fallbackLng: DEFAULT_LANGUAGE,
  interpolation: { escapeValue: false },
})

export default i18n
