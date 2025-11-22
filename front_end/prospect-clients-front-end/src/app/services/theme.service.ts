import { Injectable, signal } from '@angular/core';

type ThemeMode = 'light' | 'dark';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly storageKey = 'app-theme';
  public readonly mode = signal<ThemeMode>('light');

  constructor() {
    const saved = (localStorage.getItem(this.storageKey) as ThemeMode) || null;
    if (saved === 'dark' || saved === 'light') {
      this.setMode(saved);
    } else {
      this.setMode('light');
    }
  }

  toggle(): void {
    this.setMode(this.mode() === 'dark' ? 'light' : 'dark');
  }

  setMode(next: ThemeMode): void {
    this.mode.set(next);
    document.body.setAttribute('data-theme', next);
    localStorage.setItem(this.storageKey, next);
  }
}


