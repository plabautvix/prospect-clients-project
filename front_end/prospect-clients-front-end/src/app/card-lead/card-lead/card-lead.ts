import { Component, input, InputSignal, inject, EventEmitter, Output, signal, computed } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { SendMessageDialog } from '../send-message-dialog/send-message-dialog';
import { WhatsappApiService } from '../../services/whatsapp-api.service';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-card-lead',
  imports: [MatCardModule, MatIconModule, MatButtonModule, MatCheckboxModule, CommonModule],
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
  public avaliacao: InputSignal<string | null | undefined> = input<string | null | undefined>(null);
  public quantidade_avaliacoes: InputSignal<string | null | undefined> = input<string | null | undefined>(null);

  private dialog = inject(MatDialog);
  private whatsappApi = inject(WhatsappApiService);

  public readonly isSelected = signal<boolean>(false);
  @Output() selectedChange = new EventEmitter<{ selected: boolean; telefone: string; lead: { nome: string; endereco: string; telefone: string; site: string | null; foto: string | null } }>();

  // Compute full/half/empty stars for display
  public starArray = computed(() => {
    const ratingStr = this.avaliacao();
    if (!ratingStr) return [];
    
    const score = parseFloat(ratingStr.replace(',', '.'));
    if (isNaN(score)) return [];

    const stars = [];
    for (let i = 1; i <= 5; i++) {
      if (score >= i) {
        stars.push('star');
      } else if (score >= i - 0.5) {
        stars.push('star_half');
      } else {
        stars.push('star_border');
      }
    }
    return stars;
  });

  toggleSelected(next: boolean): void {
    this.isSelected.set(next);
    this.selectedChange.emit({
      selected: next,
      telefone: this.telefone() || '',
      lead: {
        nome: this.nome() || '',
        endereco: this.endereco() || '',
        telefone: this.telefone() || '',
        site: this.site() || null,
        foto: this.foto() || null
      }
    });
  }

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
