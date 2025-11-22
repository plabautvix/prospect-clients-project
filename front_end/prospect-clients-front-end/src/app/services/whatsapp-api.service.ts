import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface LeadPayload {
  nome: string | null | undefined;
  endereco: string | null | undefined;
  telefone: string | null | undefined;
  site: string | null | undefined;
}

@Injectable({ providedIn: 'root' })
export class WhatsappApiService {
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:3000';

  sendCustomMessage(lead: LeadPayload, message: string) {
    return this.http.post<{ ok: boolean }>(`${this.baseUrl}/api/send`, {
      lead,
      message
    });
  }

  sendBatchMessage(leads: LeadPayload[], message: string) {
    return this.http.post<{ ok: boolean; total: number; sent: number; failed: number }>(
      `${this.baseUrl}/api/send-batch`,
      { leads, message }
    );
  }

  getSentSummary() {
    return this.http.get<{ ok: boolean; total: number; sent: number; failed: number }>(
      `${this.baseUrl}/api/sent/summary`
    );
  }

  getSentLog(limit = 100) {
    return this.http.get<{ ok: boolean; total: number; items: any[] }>(
      `${this.baseUrl}/api/sent/log`,
      { params: { limit } as any }
    );
  }
}


