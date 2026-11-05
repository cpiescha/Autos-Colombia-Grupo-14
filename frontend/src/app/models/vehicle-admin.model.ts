export type TipoVehiculoAdmin = 'MOTO' | 'CARRO' | 'CAMIONETA';

export interface ClienteOpcion {
  id: number;
  nombre: string;
}

export interface VehiculoEscritura {
  placa: string;
  tipo: TipoVehiculoAdmin;
  marca: string;
  modelo: string;
  color: string;
  cliente_id: number;
}

export interface VehiculoGuardado extends VehiculoEscritura {
  id: number;
  activo: boolean;
}

export interface VehiculoDetalle extends VehiculoEscritura {
  activo: boolean;
  estado_mensualidad: 'vigente' | 'vencida';
  authorized: boolean;
  rejection_reason: string | null;
}
