import { Component , inject} from '@angular/core';
import { Userservice } from '../services/userservice/userservice';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import { CardLead } from '../card-lead/card-lead/card-lead';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
interface Lead {
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
  public searchText: FormControl<string | null> = new FormControl('');
  public leadsList: Lead[] = [];
  public getLeads($event: Event): void {
    $event.preventDefault();
    this.userService.getUserInfo(this.searchText.value ?? '').subscribe(
        response => {
          console.log(response, "toper");
          this.leadsList = response;
        }
      );
  }

}
