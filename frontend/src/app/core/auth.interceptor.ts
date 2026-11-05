import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const api = req.url.startsWith('/api/');
  const login = req.url === '/api/auth/login';
  const token = api && !login ? auth.token() : null;
  const peticion = token && !req.headers.has('Authorization')
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(peticion).pipe(
    catchError((error: HttpErrorResponse) => {
      // Do not recursively call logout, or let an old request invalidate a new session.
      if (error.status === 401 && api && !login && token && token === auth.token()) {
        auth.invalidar(true, 'La sesión no es válida o venció. Inicie sesión nuevamente.');
      }
      return throwError(() => error);
    })
  );
};
