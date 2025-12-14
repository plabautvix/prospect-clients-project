"use client"

import { useState } from "react"
import { useAuth, AuthProvider } from "@/contexts/auth-context"
import { LoginForm, RegisterForm } from "@/components/login-form"
import { Dashboard } from "@/components/dashboard"
import { Prospectinho } from "@/components/prospectinho"
import { Loader2 } from "lucide-react"

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth()
  const [isLoginMode, setIsLoginMode] = useState(true)

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background">
        <Prospectinho size="lg" mood="thinking" className="mb-6 animate-bounce-gentle" />
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground font-bold">Carregando...</p>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Dashboard />
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4 py-12">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-black text-primary tracking-tight mb-2">Prospecta</h1>
        <p className="text-muted-foreground font-medium">Automatize sua prospecção de leads</p>
      </div>

      {isLoginMode ? (
        <LoginForm onToggleMode={() => setIsLoginMode(false)} />
      ) : (
        <RegisterForm onToggleMode={() => setIsLoginMode(true)} />
      )}

      <p className="mt-8 text-sm text-muted-foreground text-center max-w-md">
        Prospecção inteligente via Google Maps, Instagram e muito mais. Em breve!
      </p>
    </div>
  )
}

export default function Home() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
