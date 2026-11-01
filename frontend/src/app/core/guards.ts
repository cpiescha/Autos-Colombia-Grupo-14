import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { Rol } from '../models/auth.model';

// Solo entra quien tiene sesión
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.autenticado() ? true : inject(Router).createUrlTree(['/login']);
};

// Si ya hay sesión, no deja volver al login
export const loginGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.autenticado() ? inject(Router).createUrlTree([auth.rutaInicial()]) : true;
};

// Revisa data.roles de la ruta
export const rolGuard: CanActivateFn = (route) => {
  const auth = inject(AuthService);
  const roles = route.data['roles'] as Rol[] | undefined;
  const rol = auth.rol();
  if (!roles || (rol && roles.includes(rol))) return true;
  return inject(Router).createUrlTree(['/acceso-denegado']);
};