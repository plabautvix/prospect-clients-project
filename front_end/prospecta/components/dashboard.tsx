"use client"

import { useEffect, useState, useCallback } from "react"
import { useAuth } from "@/contexts/auth-context"
import { apiClient, type Operation } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { NewOperationForm } from "@/components/new-operation-form"
import { OperationsList } from "@/components/operations-list"
import { WhatsAppQR } from "@/components/whatsapp-qr"
import { LeadSearch } from "@/components/lead-search"
import { Prospectinho, FloatingProspectinho } from "@/components/prospectinho"
import { Loader2, LogOut, RefreshCw, Zap, TrendingUp, CheckCircle2, Target, Home, Settings } from "lucide-react"
import { cn } from "@/lib/utils"

type Tab = "home" | "operations"

export function Dashboard() {
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState<Tab>("home")
  const [operations, setOperations] = useState<Operation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isWhatsAppConnected, setIsWhatsAppConnected] = useState(false)

  const fetchOperations = useCallback(async () => {
    try {
      const data = await apiClient.getOperations()
      setOperations(data)
    } catch (error) {
      console.error("Erro ao buscar operações:", error)
    }
  }, [])

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      await fetchOperations()
      setIsLoading(false)
    }
    loadData()
  }, [fetchOperations])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await fetchOperations()
    setIsRefreshing(false)
  }

  const activeCount = operations.filter((op) =>
    ["running", "active", "ativo"].includes(op.status?.toLowerCase()),
  ).length

  const completedCount = operations.filter((op) => ["completed", "concluido"].includes(op.status?.toLowerCase())).length

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-primary text-primary-foreground shadow-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Prospectinho size="sm" mood="happy" />
            <div>
              <h1 className="text-2xl font-black tracking-tight">Prospecta</h1>
              <p className="text-sm opacity-90">Olá, {user?.name || user?.email}!</p>
            </div>
          </div>

          {/* Tabs */}
          <nav className="hidden md:flex items-center gap-2 bg-primary-foreground/10 rounded-2xl p-1">
            <button
              onClick={() => setActiveTab("home")}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-xl font-bold transition-all",
                activeTab === "home"
                  ? "bg-primary-foreground text-primary"
                  : "text-primary-foreground/80 hover:text-primary-foreground",
              )}
            >
              <Home className="h-4 w-4" />
              Início
            </button>
            <button
              onClick={() => setActiveTab("operations")}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-xl font-bold transition-all",
                activeTab === "operations"
                  ? "bg-primary-foreground text-primary"
                  : "text-primary-foreground/80 hover:text-primary-foreground",
              )}
            >
              <Settings className="h-4 w-4" />
              Operações
            </button>
          </nav>

          <Button
            variant="secondary"
            onClick={logout}
            className="rounded-2xl font-bold shadow-[0_3px_0_0_rgba(0,0,0,0.1)] hover:shadow-[0_1px_0_0_rgba(0,0,0,0.1)] hover:translate-y-0.5 transition-all"
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sair
          </Button>
        </div>

        {/* Mobile Tabs */}
        <nav className="md:hidden flex items-center gap-2 px-4 pb-4">
          <button
            onClick={() => setActiveTab("home")}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-xl font-bold transition-all",
              activeTab === "home"
                ? "bg-primary-foreground text-primary"
                : "bg-primary-foreground/10 text-primary-foreground/80",
            )}
          >
            <Home className="h-4 w-4" />
            Início
          </button>
          <button
            onClick={() => setActiveTab("operations")}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-xl font-bold transition-all",
              activeTab === "operations"
                ? "bg-primary-foreground text-primary"
                : "bg-primary-foreground/10 text-primary-foreground/80",
            )}
          >
            <Settings className="h-4 w-4" />
            Operações
          </button>
        </nav>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Home Tab */}
        {activeTab === "home" && (
          <div className="space-y-8">
            {/* WhatsApp Connection Section */}
            {!isWhatsAppConnected && (
              <div className="glass-card rounded-3xl overflow-hidden">
                <WhatsAppQR onAuthenticated={() => setIsWhatsAppConnected(true)} />
              </div>
            )}

            {/* Connected Status Badge */}
            {isWhatsAppConnected && (
              <div className="flex items-center justify-center gap-3 py-4">
                <div className="flex items-center gap-2 bg-[#58CC02]/20 text-[#58CC02] px-4 py-2 rounded-full font-bold">
                  <div className="h-2 w-2 rounded-full bg-[#58CC02] animate-pulse" />
                  WhatsApp Conectado
                </div>
              </div>
            )}

            {/* Lead Search */}
            <LeadSearch isWhatsAppConnected={isWhatsAppConnected} />
          </div>
        )}

        {/* Operations Tab */}
        {activeTab === "operations" && (
          <>
            {/* Stats Cards */}
            <div className="grid gap-6 md:grid-cols-3 mb-10">
              <div className="mirror-effect">
                <div className="glass-card rounded-3xl p-6 flex items-center gap-5 transition-transform hover:scale-[1.02]">
                  <div className="bg-primary/20 p-4 rounded-2xl">
                    <Target className="h-8 w-8 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-muted-foreground uppercase tracking-wide">Total</p>
                    <p className="text-4xl font-black text-foreground">{operations.length}</p>
                  </div>
                </div>
              </div>

              <div className="mirror-effect">
                <div className="glass-card rounded-3xl p-6 flex items-center gap-5 transition-transform hover:scale-[1.02] animate-pulse-glow">
                  <div className="bg-[#58CC02]/20 p-4 rounded-2xl">
                    <Zap className="h-8 w-8 text-[#58CC02]" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-muted-foreground uppercase tracking-wide">Em Execução</p>
                    <p className="text-4xl font-black text-foreground">{activeCount}</p>
                  </div>
                </div>
              </div>

              <div className="mirror-effect">
                <div className="glass-card rounded-3xl p-6 flex items-center gap-5 transition-transform hover:scale-[1.02]">
                  <div className="bg-[#1CB0F6]/20 p-4 rounded-2xl">
                    <CheckCircle2 className="h-8 w-8 text-[#1CB0F6]" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-muted-foreground uppercase tracking-wide">Concluídas</p>
                    <p className="text-4xl font-black text-foreground">{completedCount}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-6 w-6 text-primary" />
                <h2 className="text-2xl font-black text-foreground">Suas Prospecções</h2>
              </div>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className="rounded-2xl font-bold border-2 hover:bg-secondary shadow-[0_3px_0_0_rgba(0,0,0,0.05)] hover:shadow-[0_1px_0_0_rgba(0,0,0,0.05)] hover:translate-y-0.5 transition-all bg-transparent"
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                  Atualizar
                </Button>
                <NewOperationForm onSuccess={handleRefresh} />
              </div>
            </div>

            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-16">
                <Prospectinho size="lg" mood="thinking" className="mb-4" />
                <Loader2 className="h-8 w-8 animate-spin text-primary mb-2" />
                <p className="text-muted-foreground font-medium">Carregando prospecções...</p>
              </div>
            ) : (
              <OperationsList operations={operations} onRefresh={handleRefresh} />
            )}
          </>
        )}
      </main>

      <FloatingProspectinho />
    </div>
  )
}
