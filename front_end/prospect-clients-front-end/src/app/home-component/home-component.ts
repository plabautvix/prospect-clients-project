import { Component , inject, signal } from '@angular/core';
import { Userservice } from '../services/userservice/userservice';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import { CardLead } from '../card-lead/card-lead/card-lead';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { WhatsappApiService } from '../services/whatsapp-api.service';
import { BatchMessageDialog } from './batch-message-dialog/batch-message-dialog';

export interface Lead {
  nome: string;
  endereco: string;
  telefone: string;
  site: string | null;
  foto: string | null;
}

@Component({
  selector: 'app-home-component',
  imports: [MatFormFieldModule, MatInputModule, MatButtonModule, MatIconModule, CardLead, ReactiveFormsModule, RouterLink],
  standalone: true,
  templateUrl: './home-component.html',
  styleUrl: './home-component.scss'
})
export class HomeComponent {
  public userService: Userservice = inject(Userservice);
  private dialog = inject(MatDialog);
  private whatsappApi = inject(WhatsappApiService);
  public searchText: FormControl<string | null> = new FormControl('');
  public leadsList: Lead[] = [];
  private selectedMap = new Map<string, Lead>();
  public readonly selectedLeadsCount = signal<number>(0);
  public getLeads($event: Event): void {
    $event.preventDefault();
    this.userService.getUserInfo(this.searchText.value ?? '').subscribe(
        response => {
          console.log(response, "toper");
          this.leadsList = response;
        }
      );
  }

  onCardSelectedChange(e: any) {
    const lead: Lead = {
      nome: e?.lead?.nome ?? '',
      endereco: e?.lead?.endereco ?? '',
      telefone: e?.lead?.telefone ?? '',
      site: e?.lead?.site ?? null,
      foto: e?.lead?.foto ?? null
    };
    const key = (e?.telefone as string) || JSON.stringify(lead);
    if (e?.selected) this.selectedMap.set(key, lead);
    else this.selectedMap.delete(key);
    this.selectedLeadsCount.set(this.selectedMap.size);
  }

  openBatchDialog(): void {
    const ref = this.dialog.open(BatchMessageDialog);
    ref.afterClosed().subscribe((message?: string) => {
      if (!message) return;
      const leads = Array.from(this.selectedMap.values());
      this.whatsappApi.sendBatchMessage(
        leads.map(l => ({
          nome: l.nome,
          endereco: l.endereco,
          telefone: l.telefone,
          site: l.site
        })),
        message
      ).subscribe({
        next: (resp) => {
          alert(`Lote enviado: ${resp.sent}/${resp.total} com sucesso, ${resp.failed} falharam.`);
        },
        error: () => {
          alert('Falha no envio em lote. Verifique o WhatsApp services.');
        }
      });
    });
  }
}
