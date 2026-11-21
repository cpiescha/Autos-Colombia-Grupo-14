import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, forkJoin, map, of, switchMap } from 'rxjs';
import {
  Cliente,
  PagoAnularRequest,
  PagoCreate,
  PagoItem,
  RecaudoResumen,
  VigenciaMembresia,
} from '../models/payment.model';

interface ClienteApi {
  id: number;
  nombre: string;
}

interface MensualidadApi {
  vehiculo_id: number;
  cliente_id: number;
  placa: string;
  fecha_corte: string | null;
  estado: 'vigente' | 'vencido';
  fecha_ultimo_pago: string | null;
}

interface PagoApi {
  id: number;
  vehiculo_id: number;
  cliente_id: number;
  estado: string;
  valor: number;
  medio: string;
  fecha_pago: string;
  cobertura_desde?: string;
  fecha_corte: string;
  motivo_anulacion?: string | null;
  anulado_en?: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class PagosService {
  private readonly http = inject(HttpClient);

  listarClientes(busqueda?: string): Observable<Cliente[]> {
    return this.http.get<ClienteApi[]>('/api/clientes').pipe(
      map((clientes) => {
        const texto = busqueda?.trim().toLowerCase();
        return clientes
          .filter((cliente) => !texto || cliente.nombre.toLowerCase().includes(texto) || String(cliente.id) === texto)
          .map((cliente) => ({ id: cliente.id, documento: '', nombre: cliente.nombre, activo: true }));
      }),
    );
  }

  inactivarCliente(clienteId: number, motivo: string): Observable<void> {
    return this.http.patch<unknown>(`/api/clientes/${clienteId}/baja`, { motivo }).pipe(map(() => undefined));
  }

  consultarVigencia(criterio: { documento?: string; placa?: string }): Observable<VigenciaMembresia> {
    const placa = criterio.placa?.trim().toUpperCase();
    if (placa) {
      return this.http.get<MensualidadApi>(`/api/mensualidades/vehiculo/${placa}`).pipe(map((item) => this.vigencia(item)));
    }
    const texto = criterio.documento?.trim();
    if (!texto) {
      throw new Error('Ingresa una placa o el nombre del cliente.');
    }
    return this.listarClientes(texto).pipe(
      switchMap((clientes) => {
        const cliente = clientes[0];
        if (!cliente) {
          throw new Error('No hay un cliente con ese nombre.');
        }
        return this.http.get<MensualidadApi[]>(`/api/mensualidades/cliente/${cliente.id}`);
      }),
      map((items) => {
        if (!items.length) {
          throw new Error('El cliente no tiene mensualidades.');
        }
        return this.vigencia(items[0]);
      }),
    );
  }

  registrarPago(payload: PagoCreate): Observable<PagoItem> {
    const placa = payload.placa?.trim().toUpperCase();
    if (!placa) {
      throw new Error('La placa es obligatoria para registrar el pago.');
    }
    const medio = payload.metodo_pago === 'TARJETA' ? 'QR' : payload.metodo_pago;
    return this.http.get<MensualidadApi>(`/api/mensualidades/vehiculo/${placa}`).pipe(
      switchMap((mensualidad) => this.http.post<PagoApi>('/api/pagos', {
        vehiculo_id: mensualidad.vehiculo_id,
        valor: payload.monto,
        medio,
        clave_idempotencia: `web-${placa}-${Date.now()}`,
      })),
      map((pago) => this.pago(pago, placa)),
    );
  }

  listarHistorialPagos(filtros?: {
    documento?: string;
    placa?: string;
    estado?: string;
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Observable<PagoItem[]> {
    return this.http.get<PagoApi[]>('/api/pagos').pipe(
      switchMap((pagos) => this.conPlaca(pagos, filtros?.placa)),
      switchMap((pagos) => forkJoin({
        pagos: of(pagos),
        clientes: this.listarClientes().pipe(catchError(() => of([] as Cliente[]))),
      })),
      map(({ pagos, clientes }) => pagos
        .map((pago) => this.pago(pago, pago.placa, clientes))
        .filter((pago) => this.cumpleFiltro(pago, filtros))),
    );
  }

  anularPago(pagoId: number, payload: PagoAnularRequest): Observable<PagoItem> {
    return this.http.patch<PagoApi>(`/api/pagos/${pagoId}/anular`, payload).pipe(
      map((pago) => this.pago({ ...pago, fecha_pago: '', fecha_corte: '', vehiculo_id: 0, cliente_id: 0 })),
    );
  }

  consultarRecaudo(fechaInicio: string, fechaFin: string): Observable<RecaudoResumen> {
    return this.listarHistorialPagos({ fecha_inicio: fechaInicio, fecha_fin: fechaFin }).pipe(
      map((pagos) => {
        const validos = pagos.filter((pago) => pago.estado === 'REGISTRADO');
        const anulados = pagos.filter((pago) => pago.estado === 'ANULADO');
        const porMedio = new Map<string, { cantidad: number; total: number }>();
        for (const pago of validos) {
          const actual = porMedio.get(pago.metodo_pago) ?? { cantidad: 0, total: 0 };
          actual.cantidad += 1;
          actual.total += Number(pago.monto);
          porMedio.set(pago.metodo_pago, actual);
        }
        return {
          fecha_inicio: fechaInicio,
          fecha_fin: fechaFin,
          total_recaudado: validos.reduce((suma, pago) => suma + Number(pago.monto), 0),
          total_anulado: anulados.reduce((suma, pago) => suma + Number(pago.monto), 0),
          cantidad_pagos_validos: validos.length,
          cantidad_pagos_anulados: anulados.length,
          por_metodo: [...porMedio.entries()].map(([metodo_pago, valor]) => ({ metodo_pago, ...valor })),
        };
      }),
    );
  }

  mensaje(error: HttpErrorResponse | { message?: string }): string {
    const cuerpo = error instanceof HttpErrorResponse ? error.error : null;
    return cuerpo?.message || cuerpo?.detail || (error as { message?: string }).message || 'No fue posible completar la operación.';
  }

  private conPlaca(pagos: PagoApi[], placa?: string): Observable<Array<PagoApi & { placa?: string }>> {
    const normalizada = placa?.trim().toUpperCase();
    if (!normalizada) {
      return of(pagos);
    }
    return this.http.get<MensualidadApi>(`/api/mensualidades/vehiculo/${normalizada}`).pipe(
      map((mensualidad) => pagos
        .filter((pago) => pago.vehiculo_id === mensualidad.vehiculo_id)
        .map((pago) => ({ ...pago, placa: mensualidad.placa }))),
      catchError(() => of([])),
    );
  }

  private cumpleFiltro(pago: PagoItem, filtros?: {
    documento?: string;
    estado?: string;
    fecha_inicio?: string;
    fecha_fin?: string;
  }): boolean {
    if (!filtros) {
      return true;
    }
    const texto = filtros.documento?.trim().toLowerCase();
    if (texto && !`${pago.cliente_nombre ?? ''} ${pago.cliente_id ?? ''}`.toLowerCase().includes(texto)) {
      return false;
    }
    if (filtros.estado === 'PAGADO' && pago.estado !== 'REGISTRADO') {
      return false;
    }
    if (filtros.estado === 'ANULADO' && pago.estado !== 'ANULADO') {
      return false;
    }
    const fecha = pago.fecha_pago?.slice(0, 10);
    if (filtros.fecha_inicio && fecha < filtros.fecha_inicio) {
      return false;
    }
    if (filtros.fecha_fin && fecha > filtros.fecha_fin) {
      return false;
    }
    return true;
  }

  private vigencia(item: MensualidadApi): VigenciaMembresia {
    return {
      cliente_id: item.cliente_id,
      placa: item.placa,
      estado: item.estado === 'vigente' ? 'ACTIVA' : 'VENCIDA',
      fecha_fin: item.fecha_corte,
      fecha_inicio: item.fecha_ultimo_pago,
    };
  }

  private pago(pago: PagoApi, placa?: string, clientes: Cliente[] = []): PagoItem {
    return {
      id: pago.id,
      cliente_id: pago.cliente_id,
      cliente_nombre: clientes.find((cliente) => cliente.id === pago.cliente_id)?.nombre,
      placa,
      monto: Number(pago.valor),
      metodo_pago: pago.medio,
      estado: pago.estado === 'ANNULLED' ? 'ANULADO' : 'REGISTRADO',
      fecha_pago: pago.fecha_pago,
      vigencia_desde: pago.cobertura_desde,
      vigencia_hasta: pago.fecha_corte,
      motivo_anulacion: pago.motivo_anulacion,
      fecha_anulacion: pago.anulado_en,
    };
  }
}
