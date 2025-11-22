import { Component, input, InputSignal, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { SendMessageDialog } from '../send-message-dialog/send-message-dialog';
import { WhatsappApiService } from '../../services/whatsapp-api.service';

@Component({
  selector: 'app-card-lead',
  imports: [MatCardModule, MatIconModule, MatButtonModule],
  standalone: true,
  templateUrl: './card-lead.html',
  styleUrl: './card-lead.scss'
})
export class CardLead {

  public nome: InputSignal<string> = input("");
  public endereco: InputSignal<string> = input("");
  public telefone: InputSignal<string> = input("");
  public site: InputSignal<string> = input("");
  public foto: InputSignal<string> = input("");

  private dialog = inject(MatDialog);
  private whatsappApi = inject(WhatsappApiService);

  openSendDialog(): void {
    const ref = this.dialog.open(SendMessageDialog, {
      data: {
        nome: this.nome() || '',
        endereco: this.endereco() || '',
        telefone: this.telefone() || '',
        site: this.site() || ''
      }
    });
    ref.afterClosed().subscribe((message?: string) => {
      if (!message) return;
      this.whatsappApi.sendCustomMessage(
        {
          nome: this.nome(),
          endereco: this.endereco(),
          telefone: this.telefone(),
          site: this.site()
        },
        message
      ).subscribe({
        next: () => {
          // feedback simples
          alert('Mensagem enviada com sucesso pelo WhatsApp!');
        },
        error: () => {
          alert('Falha ao enviar mensagem. Verifique o WhatsApp services.');
        }
      });
    });
  }
}
