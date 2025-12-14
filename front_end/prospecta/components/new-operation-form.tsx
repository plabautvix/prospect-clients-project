"use client"

import type React from "react"

import { useState } from "react"
import { apiClient } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Prospectinho } from "@/components/prospectinho"
import { Loader2, Plus, Search, MessageSquare, Tag, Rocket } from "lucide-react"

interface NewOperationFormProps {
  onSuccess: () => void
}

export function NewOperationForm({ onSuccess }: NewOperationFormProps) {
  const [open, setOpen] = useState(false)
  const [searchText, setSearchText] = useState("")
  const [messageUser, setMessageUser] = useState("")
  const [title, setTitle] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      await apiClient.activateMapsService(searchText, messageUser, title || undefined)
      setOpen(false)
      setSearchText("")
      setMessageUser("")
      setTitle("")
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao iniciar prospecção")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="rounded-2xl font-bold bg-primary hover:bg-primary/90 shadow-[0_4px_0_0_rgba(0,0,0,0.2)] hover:shadow-[0_2px_0_0_rgba(0,0,0,0.2)] hover:translate-y-0.5 transition-all">
          <Plus className="mr-2 h-5 w-5" />
          Nova Prospecção
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg rounded-3xl border-2">
        <DialogHeader className="text-center pb-2">
          <div className="flex justify-center mb-4">
            <Prospectinho size="md" mood="excited" />
          </div>
          <DialogTitle className="text-2xl font-black">Nova Prospecção</DialogTitle>
          <DialogDescription>
            Configure sua busca e mensagem para encontrar novos leads automaticamente.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 mt-4">
          {error && (
            <div className="bg-destructive/10 text-destructive text-sm p-4 rounded-2xl border border-destructive/20 font-medium">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="title" className="text-sm font-bold">
              Título da Operação (opcional)
            </Label>
            <div className="relative">
              <Tag className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                id="title"
                type="text"
                placeholder="Ex: Prospecção Restaurantes SP"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="pl-12 h-12 rounded-2xl border-2 border-border focus:border-primary bg-secondary/30"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="searchText" className="text-sm font-bold">
              Termo de Busca
            </Label>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                id="searchText"
                type="text"
                placeholder="Ex: Restaurantes em São Paulo"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-12 h-12 rounded-2xl border-2 border-border focus:border-primary bg-secondary/30"
                required
              />
            </div>
            <p className="text-xs text-muted-foreground pl-1">Este termo será usado para buscar leads</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="messageUser" className="text-sm font-bold">
              Mensagem para os Leads
            </Label>
            <div className="relative">
              <MessageSquare className="absolute left-4 top-4 h-5 w-5 text-muted-foreground" />
              <Textarea
                id="messageUser"
                placeholder="Olá! Vi seu negócio e gostaria de..."
                value={messageUser}
                onChange={(e) => setMessageUser(e.target.value)}
                className="pl-12 min-h-[120px] rounded-2xl border-2 border-border focus:border-primary bg-secondary/30 resize-none"
                required
              />
            </div>
            <p className="text-xs text-muted-foreground pl-1">
              Esta mensagem será enviada via WhatsApp para os contatos
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              className="flex-1 h-12 rounded-2xl font-bold border-2 shadow-[0_3px_0_0_rgba(0,0,0,0.05)] hover:shadow-[0_1px_0_0_rgba(0,0,0,0.05)] hover:translate-y-0.5 transition-all bg-transparent"
              onClick={() => setOpen(false)}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              className="flex-1 h-12 rounded-2xl font-bold bg-primary hover:bg-primary/90 shadow-[0_4px_0_0_rgba(0,0,0,0.2)] hover:shadow-[0_2px_0_0_rgba(0,0,0,0.2)] hover:translate-y-0.5 transition-all"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Iniciando...
                </>
              ) : (
                <>
                  <Rocket className="mr-2 h-5 w-5" />
                  Iniciar
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
