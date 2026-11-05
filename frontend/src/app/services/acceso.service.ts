import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom, timeout } from 'rxjs';
import { AuthService } from '../core/auth.service';
import {
  Celda,
  Comprobante,
  ConsultaEntrada,
  CorreccionAuditoria,
  RegistroAcceso,
  ReporteOcupacion,
  Resultado,
  SalidaPrevia,
  TipoComprobante,
  TipoVehiculo,
  Vehiculo,
} from '../models/models';



interface ApiCelda {
  id: number;
  codigo: string;
  categoria: 'AUTOMOVIL' | 'MOTO';
  estado: 'disponible' | 'ocupada' | 'inactiva';
  placa: string | null;
  tiene_historial: boolean;
}

interface ApiMovimientoActivo {
  permanencia_id: number;
  placa: string;
  celda: string;
  fecha_entrada: string;
  comprobante?: string | null;
}

interface ApiVehiculoLookup {
  placa: string;
  tipo: string;
  marca: string;
  modelo: string;
  color: string;
  estado_mensualidad: 'vigente' | 'vencida';
  authorized: boolean;
  rejection_reason: string | null;
}

interface ApiEntradaResponse {
  permanencia_id: number;
  placa: string;
  celda: string;
  comprobante: string;
  fecha_entrada: string;
}

interface ApiSalidaPreview {
  permanencia_id: number;
  placa: string;
  celda: string;
  fecha_entrada: string;
}

interface ApiSalidaResponse extends ApiSalidaPreview {
  fecha_salida: string;
}

interface ApiReporteOcupacion {
  vehiculos_registrados: number;
  vehiculos_presentes: number;
  moto: { capacidad: number; ocupadas: number; disponibles: number };
  automovil: { capacidad: number; ocupadas: number; disponibles: number };
  total: { capacidad: number; ocupadas: number; disponibles: number };
}

interface ApiCorreccionResponse {
  movimiento_id: number;
  celda_anterior: string;
  celda_nueva: string;
  operario_id: number;
  fecha_correccion: string;
}

function mapearTipo(tipo: string): TipoVehiculo {
  return tipo.toUpperCase().includes('MOTO') ? 'MOTO' : 'CARRO';
}

function mapearEstadoCelda(estado: ApiCelda['estado']): Celda['estado'] {
  return estado === 'disponible' ? 'LIBRE' : estado === 'ocupada' ? 'OCUPADA' : 'INACTIVA';
}

@Injectable({ providedIn: 'root' })
export class AccesoService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  readonly cargandoDatos = signal(false);
  readonly errorDatos = signal('');
  private carga?: Promise<boolean>;
  private readonly baseUrl = '/api';

  private readonly cacheVehiculos = new Map<string, Vehiculo>();

  readonly celdas = signal<Celda[]>([]);
  readonly registros = signal<RegistroAcceso[]>([]);
  readonly correcciones = signal<CorreccionAuditoria[]>([]);

  readonly activos = computed(() => this.registros().filter((r) => !r.salida));
  readonly libres = computed(() => this.celdas().filter((c) => c.estado === 'LIBRE').length);
  readonly ocupadas = computed(() => this.celdas().filter((c) => c.estado === 'OCUPADA').length);

  normalizar(placa: string): string {
    return placa.trim().toUpperCase().replace(/\s+/g, '');
  }

  cargarDatos(): Promise<boolean> {
    return this.carga ??= this.actualizarDatos().finally(() => { this.carga = undefined; });
  }

  private async actualizarDatos(): Promise<boolean> {
    this.cargandoDatos.set(true);
    this.errorDatos.set('');
    try {
      const [celdasApi, movimientosApi] = await Promise.all([
        firstValueFrom(this.http.get<ApiCelda[]>(`${this.baseUrl}/celdas`).pipe(timeout(15000))),
        firstValueFrom(this.http.get<ApiMovimientoActivo[]>(`${this.baseUrl}/movimientos/activos`).pipe(timeout(15000))),
      ]);

      const celdasMapeadas: Celda[] = celdasApi.map((c) => ({
        codigo: c.codigo,
        tipoVehiculo: mapearTipo(c.categoria),
        estado: mapearEstadoCelda(c.estado),
      }));
      this.celdas.set(celdasMapeadas);

      const registrosMapeados: RegistroAcceso[] = movimientosApi.map((m) => {
        const fechaEntrada = new Date(m.fecha_entrada);
        const numComprobante = m.comprobante ?? 'No disponible';
        return {
          id: m.permanencia_id,
          placa: m.placa,
          celda: m.celda,
          entrada: fechaEntrada,
          operario: undefined,
          comprobanteEntrada: {
            numero: numComprobante,
            tipo: 'ENTRADA' as TipoComprobante,
            fechaEmision: fechaEntrada,
          },
        };
      });
      this.registros.set(registrosMapeados);
      return true;
    } catch (err) {
      this.errorDatos.set(this.mensajeError(err));
      return false;
    } finally {
      this.cargandoDatos.set(false);
    }
  }

  obtenerVehiculo(placa: string): Vehiculo | undefined {
    return this.cacheVehiculos.get(this.normalizar(placa));
  }

  async buscarVehiculo(placa: string): Promise<Vehiculo | undefined> {
    const norm = this.normalizar(placa);
    if (this.cacheVehiculos.has(norm)) {
      return this.cacheVehiculos.get(norm);
    }
    try {
      const vApi = await firstValueFrom(
        this.http.get<ApiVehiculoLookup>(`${this.baseUrl}/vehiculos/${norm}`)
      );
      const v: Vehiculo = {
        placa: vApi.placa,
        tipo: mapearTipo(vApi.tipo),
        marca: vApi.marca,
        color: vApi.color,
        modelo: vApi.modelo,
        mensualidadFin: new Date(),
      };
      this.cacheVehiculos.set(norm, v);
      return v;
    } catch {
      // Vehicle details enrich the correction screen but are not required to correct a cell.
      return undefined;
    }
  }

  async consultarEntrada(placa: string): Promise<ConsultaEntrada> {
    const norm = this.normalizar(placa);
    if (!norm) {
      return { estado: 'NO_REGISTRADO', mensaje: 'Escriba una placa para consultar.' };
    }

    if (!await this.cargarDatos()) {
      return { estado: 'NO_REGISTRADO', mensaje: this.errorDatos() };
    }

    try {
      const vApi = await firstValueFrom(
        this.http.get<ApiVehiculoLookup>(`${this.baseUrl}/vehiculos/${norm}`)
      );

      const vehiculo: Vehiculo = {
        placa: vApi.placa,
        tipo: mapearTipo(vApi.tipo),
        marca: vApi.marca,
        color: vApi.color,
        modelo: vApi.modelo,
        mensualidadFin: vApi.estado_mensualidad === 'vigente'
          ? new Date(Date.now() + 30 * 86_400_000)
          : new Date(Date.now() - 5 * 86_400_000),
      };
      this.cacheVehiculos.set(norm, vehiculo);

      if (!vApi.authorized) {
        if (vApi.rejection_reason === 'El vehículo ya tiene una permanencia abierta.') {
          const abierto = this.activos().find((r) => r.placa === vehiculo.placa);
          return {
            estado: 'YA_DENTRO',
            vehiculo,
            celdaActual: abierto?.celda,
            mensaje: 'Este vehículo ya tiene una permanencia abierta. No se puede registrar otra entrada.',
          };
        }
        if (
          vApi.estado_mensualidad === 'vencida' ||
          vApi.rejection_reason === 'La mensualidad no está vigente.'
        ) {
          return {
            estado: 'VENCIDA',
            vehiculo,
            mensaje: 'Mensualidad vencida. El vehículo no está autorizado para ingresar.',
          };
        }
        return {
          estado: 'NO_REGISTRADO',
          vehiculo,
          mensaje: vApi.rejection_reason || 'Vehículo no autorizado.',
        };
      }

      const delTipo = this.celdas().filter((c) => c.tipoVehiculo === vehiculo.tipo && c.estado !== 'INACTIVA');
      if (!delTipo.some((c) => c.estado === 'LIBRE')) {
        const etiqueta = vehiculo.tipo === 'MOTO' ? 'motos' : 'automóviles';
        return {
          estado: 'SIN_CUPO',
          vehiculo,
          mensaje: `No hay celdas disponibles para este tipo de vehículo (${etiqueta} ${delTipo.length}/${delTipo.length}).`,
        };
      }

      return { estado: 'AUTORIZADO', vehiculo, mensaje: '' };
    } catch (err: any) {
      if (err instanceof HttpErrorResponse && err.status === 404) {
        return {
          estado: 'NO_REGISTRADO',
          mensaje: 'El vehículo no está registrado. No se permite el ingreso. No se modificó la ocupación.',
        };
      }
      return {
        estado: 'NO_REGISTRADO',
        mensaje: this.mensajeError(err),
      };
    }
  }

  async confirmarEntrada(placa: string): Promise<Resultado<RegistroAcceso>> {
    const norm = this.normalizar(placa);
    try {
      const res = await firstValueFrom(
        this.http.post<ApiEntradaResponse>(`${this.baseUrl}/entradas`, {
          placa: norm,
        })
      );

      const fechaEntrada = new Date(res.fecha_entrada);
      const registro: RegistroAcceso = {
        id: res.permanencia_id,
        placa: res.placa,
        celda: res.celda,
        entrada: fechaEntrada,
        operario: this.auth.sesion()?.nombre,
        comprobanteEntrada: {
          numero: res.comprobante,
          tipo: 'ENTRADA',
          fechaEmision: fechaEntrada,
        },
      };

      this.registros.update((l) => [...l.filter((r) => r.id !== registro.id), registro]);
      this.cambiarEstadoCelda(registro.celda, 'OCUPADA');
      await this.cargarDatos();

      return { ok: true, mensaje: 'Entrada registrada correctamente.', dato: registro };
    } catch (err: any) {
      const mensaje = this.mensajeError(err);
      return { ok: false, mensaje };
    }
  }

  async consultarSalida(comprobante: string): Promise<Resultado<SalidaPrevia>> {
    const codigo = comprobante.trim();
    if (!codigo) {
      return { ok: false, mensaje: 'El comprobante es obligatorio.' };
    }

    try {
      const res = await firstValueFrom(
        this.http.get<ApiSalidaPreview>(`${this.baseUrl}/salidas/comprobantes/${encodeURIComponent(codigo)}`)
      );
      return {
        ok: true,
        mensaje: 'Comprobante válido.',
        dato: {
          permanenciaId: res.permanencia_id,
          placa: res.placa,
          celda: res.celda,
          fechaEntrada: new Date(res.fecha_entrada),
        },
      };
    } catch (err: any) {
      return { ok: false, mensaje: this.mensajeError(err) };
    }
  }

  async registrarSalida(comprobante: string): Promise<Resultado<RegistroAcceso>> {
    const codigoComprobante = comprobante.trim();
    if (!codigoComprobante) {
      return { ok: false, mensaje: 'El comprobante es obligatorio.' };
    }

    try {
      const res = await firstValueFrom(
        this.http.post<ApiSalidaResponse>(`${this.baseUrl}/salidas`, {
          comprobante: codigoComprobante,
        })
      );

      const fechaEntrada = new Date(res.fecha_entrada);
      const fechaSalida = new Date(res.fecha_salida);
      const cerrado: RegistroAcceso = {
        id: res.permanencia_id,
        placa: res.placa,
        celda: res.celda,
        entrada: fechaEntrada,
        salida: fechaSalida,
        operario: this.auth.sesion()?.nombre,
        comprobanteEntrada: {
          numero: codigoComprobante,
          tipo: 'ENTRADA',
          fechaEmision: fechaEntrada,
        },

      };

      await this.cargarDatos();
      return { ok: true, mensaje: 'Salida registrada. La celda quedó libre.', dato: cerrado };
    } catch (err: any) {
      const mensaje = this.mensajeError(err);
      return { ok: false, mensaje };
    }
  }

  async obtenerReporteOcupacion(): Promise<Resultado<ReporteOcupacion>> {
    try {
      const res = await firstValueFrom(
        this.http.get<ApiReporteOcupacion>(`${this.baseUrl}/reportes/ocupacion`)
      );
      return {
        ok: true,
        mensaje: 'Reporte actualizado.',
        dato: {
          vehiculosRegistrados: res.vehiculos_registrados,
          vehiculosPresentes: res.vehiculos_presentes,
          moto: res.moto,
          automovil: res.automovil,
          total: res.total,
        },
      };
    } catch (err: any) {
      return {
        ok: false,
        mensaje: this.mensajeError(err),
      };
    }
  }

  permanencia(r: RegistroAcceso): string {
    const fin = r.salida ?? new Date();
    const min = Math.max(0, Math.round((fin.getTime() - r.entrada.getTime()) / 60_000));
    return `${Math.floor(min / 60)} h ${min % 60} min`;
  }

  private cambiarEstadoCelda(codigo: string, estado: Celda['estado']): void {
    this.celdas.update((l) => l.map((c) => (c.codigo === codigo ? { ...c, estado } : c)));
  }

  celdasCompatibles(idRegistro: number): Celda[] {
    const registro = this.registros().find((r) => r.id === idRegistro && !r.salida);
    if (!registro) return [];
    const tipo = this.tipoCelda(registro.celda);
    if (!tipo) return [];
    return this.celdas().filter((c) => c.estado === 'LIBRE' && c.tipoVehiculo === tipo);
  }

  tipoCelda(codigo: string): TipoVehiculo | undefined {
    return this.celdas().find(c => c.codigo === codigo)?.tipoVehiculo;
  }

  private mensajeError(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      const detalle = error.error?.message ?? error.error?.detail;
      if (typeof detalle === 'string') return detalle;
      if (error.status === 401) return 'La sesión venció. Inicie sesión nuevamente.';
      if (error.status === 403) return 'No tiene permisos para esta operación.';
    }
    return 'No fue posible completar la solicitud. Intente nuevamente.';
  }

  async corregirCelda(idRegistro: number, codigoNuevo: string): Promise<Resultado<CorreccionAuditoria>> {
    const registro = this.registros().find((r) => r.id === idRegistro && !r.salida);
    if (!registro) {
      return { ok: false, mensaje: 'No se encontró la permanencia abierta a corregir.' };
    }
    const anterior = registro.celda;
    const nueva = codigoNuevo.trim().toUpperCase();
    if (!this.celdasCompatibles(idRegistro).some(c => c.codigo === nueva)) {
      return { ok: false, mensaje: 'Seleccione una celda activa, libre y compatible. El servidor validará la disponibilidad al guardar.' };
    }
    if (nueva === anterior) {
      return { ok: false, mensaje: 'La nueva celda debe ser diferente a la actual.' };
    }

    try {
      const res = await firstValueFrom(
        this.http.patch<ApiCorreccionResponse>(
          `${this.baseUrl}/movimientos/${idRegistro}/celda`,
          {
            celda: nueva,
          }
        )
      );

      const auditoria: CorreccionAuditoria = {
        idRegistro: res.movimiento_id,
        placa: registro.placa,
        celdaAnterior: res.celda_anterior,
        celdaNueva: res.celda_nueva,
        operario: this.auth.sesion()?.nombre,
        fecha: new Date(res.fecha_correccion),
      };

      this.correcciones.update((l) => [...l, auditoria]);
      await this.cargarDatos();

      return {
        ok: true,
        mensaje: `Celda actualizada de ${res.celda_anterior} a ${res.celda_nueva}.`,
        dato: auditoria,
      };
    } catch (err: any) {
      const mensaje = this.mensajeError(err);
      return { ok: false, mensaje };
    }
  }
}
