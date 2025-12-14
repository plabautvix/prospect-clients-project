"use client"

import { useState } from "react"
import { type Operation, apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Prospectinho } from "@/components/prospectinho"
import { Loader2, StopCircle, Trash2, MessageSquare, Calendar, MapPin, Sparkles } from "lucide-react"

interface OperationsListProps {
  operations: Operation[]
  onRefresh: () => void
}

function getStatusBadge(status: string) {
  switch (status?.toLowerCase()) {
    case "running":
    case "active":
    case "ativo":
      return (
        <Badge className="bg-[#58CC02] hover:bg-[#58CC02]/90 text-white font-bold rounded-full px-3 py-1 shadow-sm">
          Em Execução
        </Badge>
      )
    case "stopped":
    case "parado":
      return <Badge className="bg-muted text-muted-foreground font-bold rounded-full px-3 py-1">Parado</Badge>
    case "completed":
    case "concluido":
      return (
        <Badge className="bg-[#1CB0F6] hover:bg-[#1CB0F6]/90 text-white font-bold rounded-full px-3 py-1 shadow-sm">
          Concluído
        </Badge>
      )
    case "error":
    case "erro":
      return (
        <Badge className="bg-destructive hover:bg-destructive/90 text-destructive-foreground font-bold rounded-full px-3 py-1">
          Erro
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" className="font-bold rounded-full px-3 py-1">
          {status || "Desconhecido"}
        </Badge>
      )
  }
}

function OperationCard({ operation, onRefresh }: { operation: Operation; onRefresh: () => void }) {
  const [isStoppingOperation, setIsStoppingOperation] = useState(false)
  const [isDeletingOperation, setIsDeletingOperation] = useState(false)

  const handleStop = async () => {
    setIsStoppingOperation(true)
    try {
      await apiClient.deactivateMapsService(operation.id)
      onRefresh()
    } catch (error) {
      console.error("Erro ao parar operação:", error)
    } finally {
      setIsStoppingOperation(false)
    }
  }

  const handleDelete = async () => {
    setIsDeletingOperation(true)
    try {
      await apiClient.deleteOperation(operation.id)
      onRefresh()
    } catch (error) {
      console.error("Erro ao deletar operação:", error)
    } finally {
      setIsDeletingOperation(false)
    }
  }

  const isRunning = ["running", "active", "ativo"].includes(operation.status?.toLowerCase())

  return (
    <div className="bg-card rounded-3xl border-2 border-border/50 shadow-lg overflow-hidden transition-all hover:shadow-xl hover:scale-[1.01]">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="space-y-1">
            <h3 className="text-lg font-black text-foreground">{operation.title || `Operação #${operation.id}`}</h3>
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4" />
              {new Date(operation.created_at).toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
          {getStatusBadge(operation.status)}
        </div>

        <div className="space-y-3 mb-5">
          <div className="flex items-start gap-3 text-sm bg-secondary/50 rounded-2xl p-3">
            <MapPin className="h-5 w-5 text-primary mt-0.5 shrink-0" />
            <div>
              <span className="font-bold text-foreground">Busca:</span>{" "}
              <span className="text-muted-foreground">{operation.search_text}</span>
            </div>
          </div>
          <div className="flex items-start gap-3 text-sm bg-secondary/50 rounded-2xl p-3">
            <MessageSquare className="h-5 w-5 text-[#1CB0F6] mt-0.5 shrink-0" />
            <div>
              <span className="font-bold text-foreground">Mensagem:</span>{" "}
              <span className="text-muted-foreground line-clamp-2">{operation.message_user}</span>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          {isRunning && (
            <Button
              variant="outline"
              onClick={handleStop}
              disabled={isStoppingOperation}
              className="flex-1 rounded-2xl font-bold border-2 hover:bg-accent/50 shadow-[0_3px_0_0_rgba(0,0,0,0.05)] hover:shadow-[0_1px_0_0_rgba(0,0,0,0.05)] hover:translate-y-0.5 transition-all bg-transparent"
            >
              {isStoppingOperation ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <StopCircle className="mr-2 h-4 w-4" />
              )}
              Parar
            </Button>
          )}

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                className="flex-1 rounded-2xl font-bold border-2 border-destructive/30 text-destructive hover:bg-destructive/10 shadow-[0_3px_0_0_rgba(0,0,0,0.05)] hover:shadow-[0_1px_0_0_rgba(0,0,0,0.05)] hover:translate-y-0.5 transition-all bg-transparent"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Excluir
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="rounded-3xl">
              <AlertDialogHeader>
                <AlertDialogTitle className="font-black text-xl">Excluir operação?</AlertDialogTitle>
                <AlertDialogDescription>
                  Esta ação não pode ser desfeita. A operação será permanentemente excluída.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel className="rounded-2xl font-bold">Cancelar</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="rounded-2xl font-bold bg-destructive hover:bg-destructive/90"
                >
                  {isDeletingOperation ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Excluir
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  )
}

export function OperationsList({ operations, onRefresh }: OperationsListProps) {
  if (operations.length === 0) {
    return (
      <div className="bg-card rounded-3xl border-2 border-dashed border-border p-12 text-center">
        <Prospectinho size="lg" mood="thinking" className="mx-auto mb-6" />
        <div className="flex items-center justify-center gap-2 mb-2">
          <Sparkles className="h-5 w-5 text-accent" />
          <h3 className="text-xl font-black text-foreground">Nenhuma prospecção ainda</h3>
          <Sparkles className="h-5 w-5 text-accent" />
        </div>
        <p className="text-muted-foreground max-w-sm mx-auto">
          Clique em "Nova Prospecção" para começar a encontrar novos leads automaticamente!
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {operations.map((operation) => (
        <OperationCard key={operation.id} operation={operation} onRefresh={onRefresh} />
      ))}
    </div>
  )
}
