import { Component, inject, signal } from '@angular/core';
import { RouterOutlet, RouterLink} from '@angular/router';
import { AuthForm } from './auth/auth-form/auth-form';
import {Userservice} from './services/userservice/userservice';
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrls: ['./app.scss']
})
export class App {
  protected readonly title = signal('prospect-clients-front-end');
  protected userService: Userservice = inject(Userservice);
}
