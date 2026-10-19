import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false)

  const login = useCallback(async (username, password) => {
    const tokenResponse = await api.post('/auth/token/', {
      username,
      password,
    })

    const token = tokenResponse.data.access
    setAccessToken(token)

    try {
      const profileResponse = await api.get('/auth/me/', {
        headers: { Authorization: `Bearer ${token}` },
      })

      setUser(profileResponse.data)
      return profileResponse.data
    } catch (error) {
      setAccessToken(null)
      setUser(null)
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    setAccessToken(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      accessToken,
      user,
      loading,
      setLoading,
      login,
      logout,
    }),
    [accessToken, user, loading, login, logout],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }

  return context
}
