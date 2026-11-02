import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-acceso-denegado',
  standalone: true,
  imports: [RouterLink],
  template: `
    <h1>Acceso denegado</h1>
    <p>Tu perfil no tiene permiso para ver esta pantalla.</p>
    <a class="boton" [routerLink]="auth.rutaInicial()">Volver al inicio</a>
  `,
})
export class AccesoDenegadoComponent {
  auth = inject(AuthService);
}