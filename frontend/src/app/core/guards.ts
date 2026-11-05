import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { Rol } from '../models/auth.model';

// Solo entra quien tiene sesión
export const authGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return await auth.restaurar() ? true : router.createUrlTree(['/login']);
};

// Si ya hay sesión, no deja volver al login
export const loginGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return await auth.restaurar() ? router.createUrlTree([auth.rutaInicial()]) : true;
};

// Revisa data.roles de la ruta
export const rolGuard: CanActivateFn = async (route) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!await auth.restaurar()) return router.createUrlTree(['/login']);
  const roles = route.data['roles'] as Rol[] | undefined;
  const rol = auth.rol();
  if (!roles || (rol && roles.includes(rol))) return true;
  return router.createUrlTree(['/acceso-denegado']);
};