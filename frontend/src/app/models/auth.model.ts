export type Rol = 'ADMINISTRADOR' | 'OPERADOR';

export interface ApiUsuario {
  id: number;
  username: string;
  name: string;
  role: Rol;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  user: ApiUsuario;
}

export interface Sesion {
  usuario: string;
  nombre: string;
  rol: Rol;
  token: string;
}