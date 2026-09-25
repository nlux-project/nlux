import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

import miscMocks from './integration/utils/miscMocks'

// jsdom does not implement ResizeObserver, which recharts'
// ResponsiveContainer (timeline graphs) requires.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

global.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver

expect.extend(matchers)

// Stub the OIDC auth library globally: components rendered without an
// <AuthProvider> (unit specs) still call useAuth() through the tree.
// Specs that need specific auth behaviour can vi.mock locally, which
// takes precedence over this setup-file mock.
vi.mock('react-oidc-context', () => ({
  AuthProvider: ({ children }: { children?: React.ReactNode }) => children,
  useAuth: () => ({
    isAuthenticated: false,
    events: {
      addListener: () => {},
      removeListener: () => {},
    },
    signinRedirect: () => {},
    signoutRedirect: () => {},
    user: undefined,
  }),
}))

beforeEach(() => {
  miscMocks()
})

afterEach(() => {
  cleanup()
})
