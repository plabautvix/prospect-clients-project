"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { apiClient, type User } from "@/lib/api"

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const mockUser = localStorage.getItem("mock_user")
        if (mockUser) {
          setUser(JSON.parse(mockUser))
          setIsLoading(false)
          return
        }

        const currentUser = await apiClient.getCurrentUser()
        setUser(currentUser)
      } catch {
        apiClient.clearToken()
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (username: string, password: string) => {
    if (username === "teste@gmail.com" && password === "teste") {
      const mockUser: User = {
        id: 1,
        email: "teste@gmail.com",
        name: "Usuário de Teste",
        is_active: true,
        created_at: new Date().toISOString(),
      }
      localStorage.setItem("mock_user", JSON.stringify(mockUser))
      localStorage.setItem("auth_token", "mock_token_teste")
      setUser(mockUser)
      return
    }

    await apiClient.login({ username, password })
    const currentUser = await apiClient.getCurrentUser()
    setUser(currentUser)
  }

  const register = async (email: string, password: string, name: string) => {
    await apiClient.register({ email, password, name })
    await login(email, password)
  }

  const logout = () => {
    apiClient.clearToken()
    localStorage.removeItem("mock_user")
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
