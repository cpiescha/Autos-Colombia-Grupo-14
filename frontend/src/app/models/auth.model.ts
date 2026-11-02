export type Rol = 'ADMINISTRADOR' | 'OPERADOR';

export interface Sesion {
  usuario: string;
  nombre: string;
  rol: Rol;
  token: string;
}