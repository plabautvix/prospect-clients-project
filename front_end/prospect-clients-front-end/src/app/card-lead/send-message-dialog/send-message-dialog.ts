import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

export interface SendMessageDialogData {
  nome: string;
  endereco: string;
  telefone: string;
  site: string;
}

@Component({
  selector: 'app-send-message-dialog',
  standalone: true,
  imports: [MatDialogModule, ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  templateUrl: './send-message-dialog.html',
  styleUrl: './send-message-dialog.scss'
})
export class SendMessageDialog {
  private dialogRef = inject(MatDialogRef<SendMessageDialog, string>);
  private data = inject<SendMessageDialogData>(MAT_DIALOG_DATA);

  message = new FormControl<string>('');

  constructor() {
    const template = [
      `Olá ${this.data?.nome || 'amigo(a)'}!`,
      'Tenho uma proposta personalizada para sua empresa com base nos seus dados:',
      '',
      'Resumo da empresa:',
      this.data?.nome ? `• Nome: ${this.data.nome}` : '',
      this.data?.endereco ? `• Endereço: ${this.data.endereco}` : '',
      this.data?.site ? `• Site: ${this.data.site}` : '',
      this.data?.telefone ? `• Telefone: ${this.data.telefone}` : '',
      '',
      'Posso te enviar mais detalhes agora?'
    ].filter(Boolean).join('\n');
    this.message.setValue(template);
  }

  close(): void {
    this.dialogRef.close();
  }

  send(): void {
    const val = (this.message.value || '').trim();
    if (!val) {
      this.dialogRef.close();
      return;
    }
    this.dialogRef.close(val);
  }
}


