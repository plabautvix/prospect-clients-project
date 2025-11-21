import { Routes } from '@angular/router';
import {AuthForm} from './auth/auth-form/auth-form';
import {authGuardGuard} from './guards/auth-guard-guard';
import { HomeComponent } from './home-component/home-component';
export const routes: Routes = [
    {
        path: '',
        canActivate: [authGuardGuard],
        component: HomeComponent,
    },
    {
        path: 'entry',
        component: AuthForm,
    },
];
