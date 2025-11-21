import { CanActivateFn , Router, UrlTree} from '@angular/router';
import { inject } from '@angular/core';
import { Userservice } from '../services/userservice/userservice';
export  const authGuardGuard: CanActivateFn = (route, state): UrlTree | boolean => {

  const userService: Userservice = inject(Userservice);
  const router: Router = inject(Router);

  if (!userService.userIsLogged()){
    return router.parseUrl('/entry');
  }

  return true;
};
