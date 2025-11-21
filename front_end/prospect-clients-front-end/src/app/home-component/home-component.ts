import { Component , inject} from '@angular/core';
import { Userservice } from '../services/userservice/userservice';


@Component({
  selector: 'app-home-component',
  imports: [],
  standalone: true,
  templateUrl: './home-component.html',
  styleUrl: './home-component.scss'
})
export class HomeComponent {
  public userService: Userservice = inject(Userservice);
}
