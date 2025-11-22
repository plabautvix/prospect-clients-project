import { Component, inject, signal } from '@angular/core';
import { RouterOutlet, RouterLink} from '@angular/router';
import { AuthForm } from './auth/auth-form/auth-form';
import {Userservice} from './services/userservice/userservice';
import { ThemeToggle } from './shared/theme-toggle/theme-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, ThemeToggle, MatButtonModule, MatIconModule],
  templateUrl: './app.html',
  styleUrls: ['./app.scss']
})
export class App {
  protected readonly title = signal('prospect-clients-front-end');
  protected userService: Userservice = inject(Userservice);
}
