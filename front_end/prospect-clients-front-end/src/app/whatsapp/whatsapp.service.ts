import { Injectable, OnDestroy, signal } from '@angular/core';

// Serviço simples que consome SSE do backend (WhatsApp services)
@Injectable({ providedIn: 'root' })
export class WhatsappService implements OnDestroy {
  private eventSource: EventSource | null = null;

  // signals para UI
  public readonly isReady = signal<boolean>(false);
  public readonly isAuthenticated = signal<boolean>(false);
  public readonly qrString = signal<string | null>(null);
  public readonly lastError = signal<string | null>(null);

  connect(streamUrl: string = 'http://localhost:3000/api/whatsapp/stream'): void {
    if (this.eventSource) {
      return;
    }
    this.eventSource = new EventSource(streamUrl, { withCredentials: false });

    const onQr = (e: MessageEvent) => {
      try {
        const qr = e.data;
        this.qrString.set(qr || null);
        this.isAuthenticated.set(false);
      } catch {
        // ignore
      }
    };

    const onReady = (e: MessageEvent) => {
      const ready = e.data === 'true' || e.data === true || e.data === '1';
      this.isReady.set(!!ready);
    };

    const onAuthenticated = (e: MessageEvent) => {
      const ok = e.data === 'true' || e.data === true || e.data === '1';
      this.isAuthenticated.set(!!ok);
      if (ok) {
        this.qrString.set(null);
      }
    };

    const onFailure = (e: MessageEvent) => {
      const msg = String(e.data || 'Falha de autenticação');
      this.lastError.set(msg);
      this.isAuthenticated.set(false);
    };

    const onDisconnected = (e: MessageEvent) => {
      const reason = String(e.data || 'desconhecido');
      this.lastError.set(`Desconectado: ${reason}`);
      this.isAuthenticated.set(false);
      this.isReady.set(false);
    };

    this.eventSource.addEventListener('qr', onQr);
    this.eventSource.addEventListener('ready', onReady);
    this.eventSource.addEventListener('authenticated', onAuthenticated);
    this.eventSource.addEventListener('auth_failure', onFailure);
    this.eventSource.addEventListener('disconnected', onDisconnected);

    this.eventSource.onerror = () => {
      this.lastError.set('Erro de conexão com WhatsApp services');
    };
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}


