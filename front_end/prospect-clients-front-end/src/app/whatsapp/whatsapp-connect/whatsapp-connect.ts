import { Component, effect, inject, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { WhatsappService } from '../whatsapp.service';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { toDataURL } from 'qrcode';

@Component({
  selector: 'app-whatsapp-connect',
  standalone: true,
  imports: [NgIf, MatIconModule, MatCardModule, MatProgressSpinnerModule],
  templateUrl: './whatsapp-connect.html',
  styleUrl: './whatsapp-connect.scss'
})
export class WhatsappConnectComponent {
  protected whatsapp = inject(WhatsappService);
  protected qrImageUrl = signal<string | null>(null);

  constructor() {
    // inicia a conexão SSE ao montar o componente
    this.whatsapp.connect();

    // gera a imagem do QR sempre que a string mudar
    effect(() => {
      const qr = this.whatsapp.qrString();
      if (qr) {
        toDataURL(qr, { width: 256, margin: 1 })
          .then((url: string) => this.qrImageUrl.set(url))
          .catch(() => this.qrImageUrl.set(null));
      } else {
        this.qrImageUrl.set(null);
      }
    });
  }
}


