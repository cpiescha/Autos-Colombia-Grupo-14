export type TipoVehiculo = 'CARRO' | 'MOTO';
export type EstadoCelda = 'LIBRE' | 'OCUPADA' | 'MANTENIMIENTO';
export type TipoComprobante = 'ENTRADA' | 'SALIDA';

export interface Cliente {
  nombres: string;
  apellidos: string;
  numeroDocumento: string;
  telefono: string;
}

export interface Mensualidad {
  fechaInicio: Date;
  fechaFin: Date;
  valor: number;
}

export interface Vehiculo {
  placa: string;
  tipo: TipoVehiculo;
  marca: string;
  color: string;
  cliente: Cliente;
  mensualidad: Mensualidad;
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
  comprobanteEntrada: Comprobante;
  comprobanteSalida?: Comprobante;
}

export interface ConsultaResultado {
  vehiculo: Vehiculo;
  mensualidadVigente: boolean;
  dentroDelParqueadero: boolean;
}

export interface Resultado<T> {
  ok: boolean;
  mensaje: string;
  dato?: T;
}
