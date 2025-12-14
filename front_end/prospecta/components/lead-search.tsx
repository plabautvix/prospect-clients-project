"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { apiClient, type Lead } from "@/lib/api"
import { Prospectinho } from "@/components/prospectinho"
import { Button } from "@/components/ui/button"
import { Loader2, Send, Search, MapPin, Phone, Globe, Check, X, MessageSquare } from "lucide-react"
import { cn } from "@/lib/utils"

interface LeadSearchProps {
  isWhatsAppConnected: boolean
}

export function LeadSearch({ isWhatsAppConnected }: LeadSearchProps) {
  const [query, setQuery] = useState("")
  const [message, setMessage] = useState("")
  const [leads, setLeads] = useState<Lead[]>([])
  const [selectedLeads, setSelectedLeads] = useState<Set<number>>(new Set())
  const [isSearching, setIsSearching] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [searchDone, setSearchDone] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px"
    }
  }, [query])

  const handleSearch = async () => {
    if (!query.trim()) return

    setIsSearching(true)
    setSearchDone(false)
    setLeads([])
    setSelectedLeads(new Set())

    try {
      const response = await apiClient.searchLeads(query)
      setLeads(response.leads)
      // Select all leads by default
      setSelectedLeads(new Set(response.leads.map((_, i) => i)))
      setSearchDone(true)
    } catch (error) {
      console.error("Erro ao buscar leads:", error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  const toggleLead = (index: number) => {
    const newSelected = new Set(selectedLeads)
    if (newSelected.has(index)) {
      newSelected.delete(index)
    } else {
      newSelected.add(index)
    }
    setSelectedLeads(newSelected)
  }

  const selectAll = () => {
    setSelectedLeads(new Set(leads.map((_, i) => i)))
  }

  const deselectAll = () => {
    setSelectedLeads(new Set())
  }

  const handleSendMessages = async () => {
    if (!message.trim() || selectedLeads.size === 0) return

    setIsSending(true)
    try {
      const selectedLeadsList = leads.filter((_, i) => selectedLeads.has(i))
      await apiClient.sendWhatsAppBatch(selectedLeadsList, message)
      // Clear after success
      setMessage("")
      setLeads([])
      setSelectedLeads(new Set())
      setSearchDone(false)
      setQuery("")
    } catch (error) {
      console.error("Erro ao enviar mensagens:", error)
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Search Input - ChatGPT style */}
      <div className="glass-card rounded-3xl p-2 mb-8">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua busca de leads... Ex: Restaurantes em São Paulo, Academias no Rio de Janeiro"
              className="w-full bg-transparent border-0 resize-none px-4 py-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-0 min-h-[56px] max-h-[200px] text-lg"
              rows={1}
            />
          </div>
          <Button
            onClick={handleSearch}
            disabled={!query.trim() || isSearching}
            className="btn-primary rounded-2xl h-12 w-12 p-0 mb-2 mr-2"
          >
            {isSearching ? <Loader2 className="h-5 w-5 animate-spin" /> : <Search className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {/* Prospectinho Helper */}
      {!searchDone && !isSearching && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Prospectinho size="lg" mood="happy" className="mb-6" />
          <h2 className="text-2xl font-black text-foreground mb-2">
            {isWhatsAppConnected ? "Pronto para prospectar!" : "Conecte o WhatsApp primeiro"}
          </h2>
          <p className="text-muted-foreground max-w-md">
            {isWhatsAppConnected
              ? "Digite acima o tipo de negócio e local que você quer prospectar. Eu vou buscar os leads para você!"
              : "Para enviar mensagens, você precisa conectar seu WhatsApp primeiro."}
          </p>
        </div>
      )}

      {/* Loading State */}
      {isSearching && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Prospectinho size="lg" mood="thinking" className="mb-4" />
          <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
          <h3 className="text-xl font-bold text-foreground">Buscando leads...</h3>
          <p className="text-muted-foreground">Estou procurando os melhores contatos para você</p>
        </div>
      )}

      {/* Results */}
      {searchDone && leads.length > 0 && (
        <div className="space-y-6">
          {/* Header with selection controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Prospectinho size="sm" mood="celebrating" />
              <div>
                <h3 className="text-xl font-bold text-foreground">Encontrei {leads.length} leads!</h3>
                <p className="text-sm text-muted-foreground">{selectedLeads.size} selecionados</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={selectAll} className="rounded-xl font-bold bg-transparent">
                <Check className="mr-1 h-4 w-4" />
                Todos
              </Button>
              <Button variant="outline" size="sm" onClick={deselectAll} className="rounded-xl font-bold bg-transparent">
                <X className="mr-1 h-4 w-4" />
                Nenhum
              </Button>
            </div>
          </div>

          {/* Leads Grid */}
          <div className="grid gap-4 md:grid-cols-2">
            {leads.map((lead, index) => (
              <div
                key={index}
                onClick={() => toggleLead(index)}
                className={cn(
                  "glass-card rounded-2xl p-4 cursor-pointer transition-all hover:scale-[1.02]",
                  selectedLeads.has(index) ? "ring-2 ring-primary bg-primary/5" : "hover:bg-secondary/50",
                )}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={cn(
                      "w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-1 transition-colors",
                      selectedLeads.has(index) ? "bg-primary border-primary" : "border-muted-foreground/30",
                    )}
                  >
                    {selectedLeads.has(index) && <Check className="h-4 w-4 text-primary-foreground" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-bold text-foreground truncate">{lead.nome}</h4>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                      <MapPin className="h-3 w-3 flex-shrink-0" />
                      <span className="truncate">{lead.endereco}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                      <Phone className="h-3 w-3 flex-shrink-0" />
                      <span>{lead.telefone}</span>
                    </div>
                    {lead.site && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                        <Globe className="h-3 w-3 flex-shrink-0" />
                        <span className="truncate">{lead.site}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Message Input */}
          {selectedLeads.size > 0 && isWhatsAppConnected && (
            <div className="glass-card rounded-3xl p-6 mt-8">
              <div className="flex items-center gap-3 mb-4">
                <MessageSquare className="h-5 w-5 text-primary" />
                <h4 className="font-bold text-foreground">Mensagem para os leads</h4>
              </div>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Digite a mensagem que será enviada para os leads selecionados..."
                className="w-full bg-secondary/50 border-0 rounded-2xl resize-none px-4 py-4 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary min-h-[120px]"
              />
              <div className="flex justify-end mt-4">
                <Button
                  onClick={handleSendMessages}
                  disabled={!message.trim() || isSending}
                  className="btn-primary rounded-2xl font-bold"
                >
                  {isSending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Enviar para {selectedLeads.size} leads
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Warning if WhatsApp not connected */}
          {selectedLeads.size > 0 && !isWhatsAppConnected && (
            <div className="glass-card rounded-3xl p-6 mt-8 border-2 border-[#FFC800]">
              <div className="flex items-center gap-4">
                <Prospectinho size="sm" mood="sad" />
                <div>
                  <h4 className="font-bold text-foreground">WhatsApp não conectado</h4>
                  <p className="text-sm text-muted-foreground">
                    Você precisa conectar o WhatsApp para enviar mensagens aos leads.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* No results */}
      {searchDone && leads.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Prospectinho size="lg" mood="sad" className="mb-4" />
          <h3 className="text-xl font-bold text-foreground mb-2">Nenhum lead encontrado</h3>
          <p className="text-muted-foreground">Tente buscar por outro termo ou localização</p>
        </div>
      )}
    </div>
  )
}
