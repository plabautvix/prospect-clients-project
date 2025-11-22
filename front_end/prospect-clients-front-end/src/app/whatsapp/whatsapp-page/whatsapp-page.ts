import { Component, inject, signal, effect } from '@angular/core';
import { NgIf } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { WhatsappService } from '../whatsapp.service';
import { toDataURL } from 'qrcode';

@Component({
  selector: 'app-whatsapp-page',
  standalone: true,
  imports: [NgIf, MatCardModule, MatButtonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './whatsapp-page.html',
  styleUrl: './whatsapp-page.scss'
})
export class WhatsappPage {
  protected whatsapp = inject(WhatsappService);
  protected qrImageUrl = signal<string | null>(null);
  protected me = signal<{ wid: string | null; pushname: string | null; platform: string | null } | null>(null);
  protected loadingMe = signal<boolean>(false);
  protected errorMe = signal<string | null>(null);

  constructor() {
    this.whatsapp.connect();

    effect(() => {
      const qr = this.whatsapp.qrString();
      if (qr) {
        toDataURL(qr, { width: 280, margin: 1 })
          .then((url: string) => this.qrImageUrl.set(url))
          .catch(() => this.qrImageUrl.set(null));
      } else {
        this.qrImageUrl.set(null);
      }
    });

    // quando autenticar, busca info do cliente
    effect(() => {
      if (this.whatsapp.isAuthenticated()) {
        this.fetchMe();
      }
    });
  }

  refreshQr(): void {
    // reconectar stream para buscar um novo QR se necessário
    this.whatsapp.disconnect();
    this.qrImageUrl.set(null);
    this.me.set(null);
    this.errorMe.set(null);
    this.whatsapp.connect();
  }

  private fetchMe(): void {
    this.loadingMe.set(true);
    this.errorMe.set(null);
    fetch('http://localhost:3000/api/whatsapp/me')
      .then(async (r) => {
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}`);
        }
        return r.json();
      })
      .then((json) => {
        if (json && json.ok) {
          this.me.set({
            wid: json.wid ?? null,
            pushname: json.pushname ?? null,
            platform: json.platform ?? null
          });
        } else {
          this.errorMe.set('Não foi possível obter seus dados do WhatsApp.');
        }
      })
      .catch(() => {
        this.errorMe.set('Erro ao buscar informações do WhatsApp.');
      })
      .finally(() => this.loadingMe.set(false));
  }
}


