import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {Router} from '@angular/router';
interface UserData {
  email: string | null;
  password: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class Userservice {
    private httpClient: HttpClient = inject(HttpClient);
    private accessToken: string | null = null;
    private userLogged: boolean = false;
    private router: Router = inject(Router);
    public userIsLogged (): boolean {
      return this.userLogged;
    }
    public getAccessToken (): string | null {
      return String(this.accessToken);
    }

    public cadastreUser (userInfo: UserData) {
      this.httpClient.post(
        'http://localhost:8000/users/', userInfo, {
          observe: 'response'
        }
      ).subscribe(response => {

        if (response.status === 201) {
          const { accessToken } = response.body as any;
          this.accessToken = accessToken;
          this.userLogged = true;
        }
        console.log('User registered successfully:', response);
      })
    }

    public loginUser (userInfo: UserData) {
      this.httpClient.post(
        'http://localhost:8000/users/login/', userInfo, {
          observe: 'response'
        }
      ).subscribe(response => {
        if (response.status === 200) {
          const { access_token } = response.body as any;
          this.accessToken = access_token;
          this.userLogged = true;
          this.router.navigate(['/']);
        }

      })
    }
  }
