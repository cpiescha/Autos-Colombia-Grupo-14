import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Cliente,
  ClienteCreate,
  ClienteUpdate,
  PagoAnularRequest,
  PagoCreate,
  PagoItem,
  RecaudoResumen,
  VigenciaMembresia,
} from '../models/payment.model';

@Injectable({
  providedIn: 'root',
})
export class PagosService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = '/api';

  // --- CLIENTES ---
  listarClientes(busqueda?: string): Observable<Cliente[]> {
    let params = new HttpParams();
    if (busqueda?.trim()) {
      params = params.set('q', busqueda.trim());
    }
    return this.http.get<Cliente[]>(`${this.apiUrl}/clients`, { params });
  }

  crearCliente(payload: ClienteCreate): Observable<Cliente> {
    return this.http.post<Cliente>(`${this.apiUrl}/clients`, payload);
  }

  actualizarCliente(clienteId: number, payload: ClienteUpdate): Observable<Cliente> {
    return this.http.patch<Cliente>(`${this.apiUrl}/clients/${clienteId}`, payload);
  }

  // --- VIGENCIA / MEMBRESÍAS ---
  consultarVigencia(criterio: {
    documento?: string;
    placa?: string;
    cliente_id?: number;
  }): Observable<VigenciaMembresia> {
    let params = new HttpParams();
    if (criterio.documento?.trim()) params = params.set('documento', criterio.documento.trim());
    if (criterio.placa?.trim()) params = params.set('placa', criterio.placa.trim().toUpperCase());
    if (criterio.cliente_id) params = params.set('cliente_id', criterio.cliente_id);
    return this.http.get<VigenciaMembresia>(`${this.apiUrl}/memberships/vigencia`, { params });
  }

  // --- PAGOS: REGISTRAR, HISTORIAL, ANULAR Y RECAUDO ---
  registrarPago(payload: PagoCreate): Observable<PagoItem> {
    return this.http.post<PagoItem>(`${this.apiUrl}/payments`, payload);
  }

  listarHistorialPagos(filtros?: {
    documento?: string;
    placa?: string;
    estado?: string;
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Observable<PagoItem[]> {
    let params = new HttpParams();
    if (filtros?.documento?.trim()) params = params.set('documento', filtros.documento.trim());
    if (filtros?.placa?.trim()) params = params.set('placa', filtros.placa.trim().toUpperCase());
    if (filtros?.estado?.trim()) params = params.set('estado', filtros.estado.trim());
    if (filtros?.fecha_inicio) params = params.set('fecha_inicio', filtros.fecha_inicio);
    if (filtros?.fecha_fin) params = params.set('fecha_fin', filtros.fecha_fin);
    return this.http.get<PagoItem[]>(`${this.apiUrl}/payments`, { params });
  }

  anularPago(pagoId: number, payload: PagoAnularRequest): Observable<PagoItem> {
    return this.http.post<PagoItem>(`${this.apiUrl}/payments/${pagoId}/annul`, payload);
  }

  consultarRecaudo(fechaInicio: string, fechaFin: string): Observable<RecaudoResumen> {
    const params = new HttpParams()
      .set('fecha_inicio', fechaInicio)
      .set('fecha_fin', fechaFin);
    return this.http.get<RecaudoResumen>(`${this.apiUrl}/payments/recaudo`, { params });
  }
}