"use client"

import type React from "react"

import { useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, Mail, Lock, User } from "lucide-react"
import { Prospectinho } from "@/components/prospectinho"

interface LoginFormProps {
  onToggleMode: () => void
}

export function LoginForm({ onToggleMode }: LoginFormProps) {
  const { login } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="w-full max-w-md">
      <div className="bg-card rounded-3xl shadow-xl border-2 border-border/50 overflow-hidden">
        <div className="bg-primary/10 px-8 pt-8 pb-4 text-center">
          <Prospectinho size="lg" mood="happy" className="mx-auto mb-4" />
          <h2 className="text-2xl font-black text-foreground">Bem-vindo de volta!</h2>
          <p className="text-muted-foreground mt-1">Entre para continuar prospectando</p>
        </div>

        <div className="p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-destructive/10 text-destructive text-sm p-4 rounded-2xl border border-destructive/20 font-medium">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-bold text-foreground">
                Email
              </Label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-12 h-14 text-base rounded-2xl border-2 border-border focus:border-primary bg-secondary/50"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-bold text-foreground">
                Senha
              </Label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-12 h-14 text-base rounded-2xl border-2 border-border focus:border-primary bg-secondary/50"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-14 text-lg font-bold rounded-2xl bg-primary hover:bg-primary/90 shadow-[0_4px_0_0_rgba(0,0,0,0.2)] hover:shadow-[0_2px_0_0_rgba(0,0,0,0.2)] hover:translate-y-0.5 transition-all"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Entrando...
                </>
              ) : (
                "ENTRAR"
              )}
            </Button>

            <p className="text-center text-sm text-muted-foreground pt-2">
              Não tem uma conta?{" "}
              <button type="button" onClick={onToggleMode} className="text-primary hover:underline font-bold">
                Cadastre-se
              </button>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}

export function RegisterForm({ onToggleMode }: LoginFormProps) {
  const { register } = useAuth()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      await register(email, password, name)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no cadastro")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="w-full max-w-md">
      <div className="bg-card rounded-3xl shadow-xl border-2 border-border/50 overflow-hidden">
        <div className="bg-primary/10 px-8 pt-8 pb-4 text-center">
          <Prospectinho size="lg" mood="excited" className="mx-auto mb-4" />
          <h2 className="text-2xl font-black text-foreground">Crie sua conta!</h2>
          <p className="text-muted-foreground mt-1">Comece a prospectar em minutos</p>
        </div>

        <div className="p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-destructive/10 text-destructive text-sm p-4 rounded-2xl border border-destructive/20 font-medium">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-bold text-foreground">
                Nome
              </Label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  id="name"
                  type="text"
                  placeholder="Seu nome"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="pl-12 h-14 text-base rounded-2xl border-2 border-border focus:border-primary bg-secondary/50"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="register-email" className="text-sm font-bold text-foreground">
                Email
              </Label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  id="register-email"
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-12 h-14 text-base rounded-2xl border-2 border-border focus:border-primary bg-secondary/50"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="register-password" className="text-sm font-bold text-foreground">
                Senha
              </Label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                <Input
                  id="register-password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-12 h-14 text-base rounded-2xl border-2 border-border focus:border-primary bg-secondary/50"
                  required
                  minLength={6}
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-14 text-lg font-bold rounded-2xl bg-primary hover:bg-primary/90 shadow-[0_4px_0_0_rgba(0,0,0,0.2)] hover:shadow-[0_2px_0_0_rgba(0,0,0,0.2)] hover:translate-y-0.5 transition-all"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Cadastrando...
                </>
              ) : (
                "CRIAR CONTA"
              )}
            </Button>

            <p className="text-center text-sm text-muted-foreground pt-2">
              Já tem uma conta?{" "}
              <button type="button" onClick={onToggleMode} className="text-primary hover:underline font-bold">
                Entrar
              </button>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
