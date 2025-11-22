import { Component, input, InputSignal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-card-lead',
  imports: [MatCardModule, MatIconModule],
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
}
