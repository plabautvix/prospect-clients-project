"use client"

import { useEffect, useState, useRef } from "react"
import { WHATSAPP_API_URL } from "@/lib/api"
import { Prospectinho } from "@/components/prospectinho"
import { Loader2, CheckCircle2, XCircle, Smartphone, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import QRCode from "react-qr-code"

type ConnectionStatus = "connecting" | "waiting_qr" | "authenticated" | "disconnected" | "error"

interface WhatsAppQRProps {
  onAuthenticated?: () => void
}

export function WhatsAppQR({ onAuthenticated }: WhatsAppQRProps) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting")
  const [qrCode, setQrCode] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const connectToStream = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setStatus("connecting")
    setError(null)
    setQrCode(null)

    const eventSource = new EventSource(`${WHATSAPP_API_URL}/api/whatsapp/stream`)
    eventSourceRef.current = eventSource

    eventSource.addEventListener("hello", () => {
      console.log("[v0] Connected to WhatsApp stream")
    })

    eventSource.addEventListener("qr", (event) => {
      console.log("[v0] QR code received:", event.data)
      let qrData = event.data
      try {
        // The server sends JSON.stringify(qr), so we need to parse it
        qrData = JSON.parse(event.data)
      } catch {
        // If it's not JSON, use as-is
      }
      setQrCode(qrData)
      setStatus("waiting_qr")
    })

    eventSource.addEventListener("authenticated", (event) => {
      console.log("[v0] Authenticated event:", event.data)
      const isAuthenticated = event.data === "true" || event.data === true || JSON.parse(event.data) === true
      if (isAuthenticated) {
        setStatus("authenticated")
        setQrCode(null)
        onAuthenticated?.()
      }
    })

    eventSource.addEventListener("ready", (event) => {
      console.log("[v0] Ready event:", event.data)
      const isReady = event.data === "true" || event.data === true || JSON.parse(event.data) === true
      if (isReady) {
        setStatus("authenticated")
        setQrCode(null)
        onAuthenticated?.()
      }
    })

    eventSource.addEventListener("auth_failure", (event) => {
      console.log("[v0] Auth failure:", event.data)
      setStatus("error")
      let errorMsg = event.data
      try {
        errorMsg = JSON.parse(event.data)
      } catch {}
      setError("Falha na autenticação: " + errorMsg)
    })

    eventSource.addEventListener("disconnected", (event) => {
      console.log("[v0] Disconnected:", event.data)
      setStatus("disconnected")
      let reason = event.data
      try {
        reason = JSON.parse(event.data)
      } catch {}
      setError("Desconectado: " + reason)
    })

    eventSource.onerror = (err) => {
      console.log("[v0] SSE connection error:", err)
      setStatus("error")
      setError("Não foi possível conectar ao serviço do WhatsApp. Verifique se o servidor está rodando na porta 3001.")
    }
  }

  useEffect(() => {
    connectToStream()

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  const handleRetry = () => {
    connectToStream()
  }

  if (status === "authenticated") {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="bg-[#58CC02]/20 p-6 rounded-full mb-6">
          <CheckCircle2 className="h-16 w-16 text-[#58CC02]" />
        </div>
        <Prospectinho size="md" mood="celebrating" className="mb-4" />
        <h3 className="text-2xl font-black text-foreground mb-2">WhatsApp Conectado!</h3>
        <p className="text-muted-foreground">Você já pode enviar mensagens para seus leads.</p>
      </div>
    )
  }

  if (status === "error" || status === "disconnected") {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="bg-[#FF4B4B]/20 p-6 rounded-full mb-6">
          <XCircle className="h-16 w-16 text-[#FF4B4B]" />
        </div>
        <Prospectinho size="md" mood="sad" className="mb-4" />
        <h3 className="text-2xl font-black text-foreground mb-2">
          {status === "disconnected" ? "Desconectado" : "Erro de Conexão"}
        </h3>
        <p className="text-muted-foreground mb-6 max-w-md">{error}</p>
        <Button onClick={handleRetry} className="btn-primary rounded-2xl font-bold">
          <RefreshCw className="mr-2 h-4 w-4" />
          Tentar Novamente
        </Button>
      </div>
    )
  }

  if (status === "connecting") {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <Prospectinho size="lg" mood="thinking" className="mb-4" />
        <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
        <h3 className="text-xl font-bold text-foreground">Conectando ao WhatsApp...</h3>
        <p className="text-muted-foreground">Aguarde enquanto estabelecemos a conexão</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="flex items-center gap-3 mb-6">
        <Smartphone className="h-8 w-8 text-primary" />
        <h3 className="text-2xl font-black text-foreground">Conectar WhatsApp</h3>
      </div>

      <Prospectinho size="sm" mood="happy" className="mb-4" />

      <p className="text-muted-foreground mb-6 max-w-md">
        Escaneie o QR Code abaixo com o WhatsApp do seu celular para conectar sua conta.
      </p>

      {qrCode && (
        <div className="bg-white p-6 rounded-3xl shadow-lg mb-6">
          <QRCode value={qrCode} size={256} level="M" />
        </div>
      )}

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <div className="h-2 w-2 rounded-full bg-[#FFC800] animate-pulse" />
        Aguardando leitura do QR Code...
      </div>
    </div>
  )
}
