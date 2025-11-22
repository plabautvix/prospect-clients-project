import { Component, inject } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { ThemeService } from '../../services/theme.service';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [MatIconModule, MatButtonModule, NgIf],
  templateUrl: './theme-toggle.html',
  styleUrl: './theme-toggle.scss'
})
export class ThemeToggle {
  protected theme = inject(ThemeService);

  toggle(): void {
    this.theme.toggle();
  }
}


