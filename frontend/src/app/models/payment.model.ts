export interface Cliente {
  id: number;
  documento: string;
  nombre: string;
  telefono?: string | null;
  correo?: string | null;
  activo: boolean;
  creado_en?: string;
}

export interface ClienteCreate {
  documento: string;
  nombre: string;
  telefono?: string;
  correo?: string;
}

export interface ClienteUpdate {
  nombre?: string;
  telefono?: string;
  correo?: string;
  activo?: boolean;
}

export interface VigenciaMembresia {
  cliente_id?: number;
  documento?: string;
  cliente_nombre?: string;
  placa?: string;
  estado: 'ACTIVA' | 'VENCIDA' | 'POR_VENCER' | 'SIN_MEMBRESIA' | string;
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
  dias_restantes?: number | null;
  mensaje?: string;
}

export interface PagoCreate {
  cliente_id?: number;
  documento?: string;
  placa?: string;
  monto: number;
  metodo_pago: 'EFECTIVO' | 'TRANSFERENCIA' | 'TARJETA' | string;
  periodo_meses?: number;
  observacion?: string;
}

export interface PagoItem {
  id: number;
  numero_recibo?: string;
  cliente_id?: number;
  cliente_nombre?: string;
  documento?: string;
  placa?: string;
  monto: number;
  metodo_pago: string;
  estado: 'PAGADO' | 'ANULADO' | string;
  fecha_pago: string;
  vigencia_desde?: string | null;
  vigencia_hasta?: string | null;
  motivo_anulacion?: string | null;
  anulado_por?: string | null;
  fecha_anulacion?: string | null;
}

export interface PagoAnularRequest {
  motivo: string;
}

export interface RecaudoPorMedio {
  metodo_pago: string;
  cantidad: number;
  total: number;
}

export interface RecaudoResumen {
  fecha_inicio: string;
  fecha_fin: string;
  total_recaudado: number;
  total_anulado: number;
  cantidad_pagos_validos: number;
  cantidad_pagos_anulados: number;
  por_metodo: RecaudoPorMedio[];
}