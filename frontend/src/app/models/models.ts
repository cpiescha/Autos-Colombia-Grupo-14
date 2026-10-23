export type TipoVehiculo = 'CARRO' | 'MOTO';
export type EstadoCelda = 'LIBRE' | 'OCUPADA' | 'MANTENIMIENTO';
export type TipoComprobante = 'ENTRADA' | 'SALIDA';

export interface Vehiculo {
  placa: string;
  tipo: TipoVehiculo;
  marca: string;
  color: string;
  modelo?: string;
  mensualidadFin: Date;
}

export interface Celda {
  codigo: string;
  tipoVehiculo: TipoVehiculo;
  estado: EstadoCelda;
}

export interface Comprobante {
  numero: string;
  tipo: TipoComprobante;
  fechaEmision: Date;
}

export interface RegistroAcceso {
  id: number;
  placa: string;
  celda: string;
  entrada: Date;
  salida?: Date;
  operario: string;
  comprobanteEntrada: Comprobante;
  comprobanteSalida?: Comprobante;
}

export type EstadoConsulta = 'AUTORIZADO' | 'NO_REGISTRADO' | 'VENCIDA' | 'YA_DENTRO' | 'SIN_CUPO';

export interface ConsultaEntrada {
  estado: EstadoConsulta;
  mensaje: string;
  vehiculo?: Vehiculo;
  celdaActual?: string;
}

export interface Resultado<T> {
  ok: boolean;
  mensaje: string;
  dato?: T;
}

export interface CorreccionAuditoria {
  idRegistro: number;
  placa: string;
  celdaAnterior: string;
  celdaNueva: string;
  operario: string;
  fecha: Date;
}
