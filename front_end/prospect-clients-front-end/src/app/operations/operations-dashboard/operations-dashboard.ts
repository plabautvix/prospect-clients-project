import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';

interface ProspectingOperation {
  id: number;
  title: string;
  region: string;
  niche: string;
  networks: string[];
  cadence: string;
  leadsPerWeek: number;
  status: 'Em execução' | 'Pausada';
}

@Component({
  selector: 'app-operations-dashboard',
  standalone: true,
  imports: [MatCardModule, MatButtonModule, MatIconModule, MatDividerModule, MatTooltipModule],
  templateUrl: './operations-dashboard.html',
  styleUrl: './operations-dashboard.scss'
})
export class OperationsDashboard {
  public readonly heroMetrics = [
    {
      icon: 'rocket_launch',
      value: '2',
      label: 'operações ativas',
      description: 'Execuções contínuas mapeando novos leads.'
    },
    {
      icon: 'insights',
      value: '312',
      label: 'leads capturados',
      description: 'Total da última semana de prospecção.'
    },
    {
      icon: 'schedule',
      value: '24/7',
      label: 'tempo de atividade',
      description: 'Monitoramento sem interrupções.'
    },
    {
      icon: 'update',
      value: '4h',
      label: 'próxima revisão',
      description: 'Ajuste automático agendado.'
    }
  ];

  public readonly operations: ProspectingOperation[] = [
    {
      id: 1,
      title: 'Odontologias premium',
      region: 'Belo Horizonte, MG',
      niche: 'Clínicas odontológicas',
      networks: ['Google Maps', 'LinkedIn'],
      cadence: 'Execução contínua (24/7)',
      leadsPerWeek: 86,
      status: 'Em execução'
    },
    {
      id: 2,
      title: 'Academias Zona Sul',
      region: 'Rio de Janeiro, RJ',
      niche: 'Academias e estúdios fitness',
      networks: ['Instagram', 'Google Business Profile', 'Facebook'],
      cadence: 'Execução contínua (24/7)',
      leadsPerWeek: 124,
      status: 'Em execução'
    },
    {
      id: 3,
      title: 'Contabilidades regionais',
      region: 'Curitiba, PR',
      niche: 'Escritórios de contabilidade',
      networks: ['LinkedIn', 'Google Maps'],
      cadence: 'Execução 08h - 22h (dias úteis)',
      leadsPerWeek: 64,
      status: 'Pausada'
    }
  ];

  public readonly networkMeta: Record<string, { iconUrl: string; background: string; text: string }> = {
    'Google Maps': {
      iconUrl: 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/googlemaps.svg',
      background: '#1A73E8',
      text: '#FFFFFF'
    },
    LinkedIn: {
      iconUrl: 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg',
      background: '#0A66C2',
      text: '#FFFFFF'
    },
    Instagram: {
      iconUrl: 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/instagram.svg',
      background: 'linear-gradient(135deg, #FCAF45, #E1306C, #5851DB)',
      text: '#FFFFFF'
    },
    Facebook: {
      iconUrl: 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/facebook.svg',
      background: '#1877F2',
      text: '#FFFFFF'
    },
    'X (Twitter)': {
      iconUrl: 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/x.svg',
      background: '#000000',
      text: '#FFFFFF'
    },
    'Google Business Profile': {
      iconUrl: 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/googlebusinessprofile.svg',
      background: '#5C6BC0',
      text: '#FFFFFF'
    },
    default: {
      iconUrl: 'https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/earth.svg',
      background: '#5C6BC0',
      text: '#FFFFFF'
    }
  };
}
