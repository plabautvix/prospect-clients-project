import { Component, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Userservice } from '../../services/userservice/userservice';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatButtonModule} from '@angular/material/button';
import {MatButtonToggleModule} from '@angular/material/button-toggle';


@Component({
  selector: 'app-auth-form',
  standalone: true,
  imports: [ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule, MatButtonToggleModule],
  templateUrl: './auth-form.html',
  styleUrl: './auth-form.scss'
})
export class AuthForm {
  email: FormControl<string | null> = new FormControl('');
  password: FormControl<string | null> = new FormControl('');
  selectedToggle: FormControl<string | null> = new FormControl('login')
  
  userService: Userservice = inject(Userservice);

  handleAction(): void {

    if (this.selectedToggle.value == 'login'){
      this.loginUser();
    }
    else {
      this.sendRegister();
    }
  }

  sendRegister(): void {
    const userData = {
      email: this.email.value,
      password: this.password.value
    };
    if (userData.email && userData.password) {
      this.userService.cadastreUser(userData);
    }
    console.log('User Data:', userData);
  }

  loginUser(): void {
    const userData = {
      email: this.email.value,
      password: this.password.value
    }

    this.userService.loginUser(
      userData
    )
  }
}
