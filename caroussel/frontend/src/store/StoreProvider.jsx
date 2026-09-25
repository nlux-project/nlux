import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react'
import { settingsStore } from './settings'

// Create context
const SettingsContext = createContext(null)

// Reducer
function settingsReducer(state, action) {
  switch (action.type) {
    case 'SET_COLLECTION':
      return { ...state, collection: action.payload }
    case 'SET_SCOPE':
      return { ...state, scope: action.payload }
    case 'SET_CONFIG':
      return { ...state, ...action.payload }
    case 'TOGGLE_COLLECTION':
      const newCollection = state.collection === 'all' ? 'all' : 'all'
      return { ...state, collection: newCollection }
    default:
      return state
  }
}

// Provider component
export default function StoreProvider({ children }) {
  const [settings, dispatch] = useReducer(settingsReducer, settingsStore.DEFAULT_STATE)

  // Sync with localStorage
  useEffect(() => {
    const stored = localStorage.getItem('nlux-carousel-settings')
    if (stored) {
      const parsed = JSON.parse(stored)
      dispatch({ type: 'SET_CONFIG', payload: parsed })
    }
  }, [])

  // Persist changes
  useEffect(() => {
    const timer = setTimeout(() => {
      localStorage.setItem('nlux-carousel-settings', JSON.stringify(settings))
    }, 500)
    return () => clearTimeout(timer)
  }, [settings])

  // Action creators
  const actions = {
    setCollection(collection) {
      dispatch({ type: 'SET_COLLECTION', payload: collection })
    },
    setScope(scope) {
      dispatch({ type: 'SET_SCOPE', payload: scope })
    },
    setConfig(config) {
      dispatch({ type: 'SET_CONFIG', payload: config })
    },
  }

  const context = {
    settings,
    ...actions,
  }

  return (
    <SettingsContext.Provider value={context}>
      {children}
    </SettingsContext.Provider>
  )
}

// Custom hook
export function useSettings() {
  const context = useContext(SettingsContext)
  if (!context) {
    throw new Error('useSettings must be used within StoreProvider')
  }
  return context
}
