import { Component } from '@angular/core';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-batch-message-dialog',
  standalone: true,
  imports: [MatDialogModule, ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  templateUrl: './batch-message-dialog.html',
  styleUrl: './batch-message-dialog.scss'
})
export class BatchMessageDialog {
  message = new FormControl<string>('Olá! Gostaria de apresentar uma proposta personalizada para sua empresa.');

  constructor(private ref: MatDialogRef<BatchMessageDialog, string>) {}

  close(): void {
    this.ref.close();
  }

  send(): void {
    const val = (this.message.value || '').trim();
    if (!val) {
      this.ref.close();
      return;
    }
    this.ref.close(val);
  }
}


