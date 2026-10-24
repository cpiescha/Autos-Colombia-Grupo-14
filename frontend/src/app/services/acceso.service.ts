import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
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

const OPERARIO_ID = 1;
const OPERARIO_NOMBRE = 'Diurno 1';
const numero = (i: number): string => String(i + 1).padStart(2, '0');

const crearCeldasIniciales = (): Celda[] => [
  ...Array.from({ length: 70 }, (_, i): Celda => ({ codigo: `A-${numero(i)}`, tipoVehiculo: 'CARRO', estado: 'LIBRE' })),
  ...Array.from({ length: 10 }, (_, i): Celda => ({ codigo: `M-${numero(i)}`, tipoVehiculo: 'MOTO', estado: 'LIBRE' })),
];

interface ApiCelda {
  codigo: string;
  categoria: string;
  estado: string;
  placa: string | null;
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

function mapearEstadoCelda(estado: string): 'LIBRE' | 'OCUPADA' {
  return estado.toLowerCase() === 'ocupada' ? 'OCUPADA' : 'LIBRE';
}

@Injectable({ providedIn: 'root' })
export class AccesoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api';

  private readonly cacheVehiculos = new Map<string, Vehiculo>();

  readonly celdas = signal<Celda[]>(crearCeldasIniciales());
  readonly registros = signal<RegistroAcceso[]>([]);
  readonly correcciones = signal<CorreccionAuditoria[]>([]);

  readonly activos = computed(() => this.registros().filter((r) => !r.salida));
  readonly libres = computed(() => this.celdas().filter((c) => c.estado === 'LIBRE').length);
  readonly ocupadas = computed(() => this.celdas().filter((c) => c.estado === 'OCUPADA').length);

  constructor() {
    this.cargarDatos();
  }

  normalizar(placa: string): string {
    return placa.trim().toUpperCase().replace(/\s+/g, '');
  }

  async cargarDatos(): Promise<void> {
    try {
      const [celdasApi, movimientosApi] = await Promise.all([
        firstValueFrom(this.http.get<ApiCelda[]>(`${this.baseUrl}/celdas`)),
        firstValueFrom(this.http.get<ApiMovimientoActivo[]>(`${this.baseUrl}/movimientos/activos`)),
      ]);

      const celdasMapeadas: Celda[] = celdasApi.map((c) => ({
        codigo: c.codigo,
        tipoVehiculo: mapearTipo(c.categoria),
        estado: mapearEstadoCelda(c.estado),
      }));
      this.celdas.set(celdasMapeadas);

      const registrosMapeados: RegistroAcceso[] = movimientosApi.map((m) => {
        const fechaEntrada = new Date(m.fecha_entrada);
        const numComprobante = m.comprobante || `AC-${m.placa}`;
        return {
          id: m.permanencia_id,
          placa: m.placa,
          celda: m.celda,
          entrada: fechaEntrada,
          operario: OPERARIO_NOMBRE,
          comprobanteEntrada: {
            numero: numComprobante,
            tipo: 'ENTRADA' as TipoComprobante,
            fechaEmision: fechaEntrada,
          },
        };
      });
      this.registros.set(registrosMapeados);
    } catch (err) {
      console.warn('Backend aún no responde en /api:', err);
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
      return undefined;
    }
  }

  async consultarEntrada(placa: string): Promise<ConsultaEntrada> {
    const norm = this.normalizar(placa);
    if (!norm) {
      return { estado: 'NO_REGISTRADO', mensaje: 'Escriba una placa para consultar.' };
    }

    await this.cargarDatos();

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

      const delTipo = this.celdas().filter((c) => c.tipoVehiculo === vehiculo.tipo);
      if (delTipo.length > 0 && !delTipo.some((c) => c.estado === 'LIBRE')) {
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
        mensaje: err?.error?.detail || err?.error?.message || 'Error al consultar el vehículo.',
      };
    }
  }

  async confirmarEntrada(placa: string): Promise<Resultado<RegistroAcceso>> {
    const norm = this.normalizar(placa);
    try {
      const res = await firstValueFrom(
        this.http.post<ApiEntradaResponse>(`${this.baseUrl}/entradas`, {
          placa: norm,
          operario_id: OPERARIO_ID,
        })
      );

      const fechaEntrada = new Date(res.fecha_entrada);
      const registro: RegistroAcceso = {
        id: res.permanencia_id,
        placa: res.placa,
        celda: res.celda,
        entrada: fechaEntrada,
        operario: OPERARIO_NOMBRE,
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
      const mensaje = err?.error?.message || 'No fue posible registrar la entrada.';
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
      return { ok: false, mensaje: err?.error?.message || err?.error?.detail || 'Comprobante inválido.' };
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
          operario_id: OPERARIO_ID,
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
        operario: OPERARIO_NOMBRE,
        comprobanteEntrada: {
          numero: codigoComprobante,
          tipo: 'ENTRADA',
          fechaEmision: fechaEntrada,
        },
        comprobanteSalida: {
          numero: `SAL-${res.permanencia_id}`,
          tipo: 'SALIDA',
          fechaEmision: fechaSalida,
        },
      };

      await this.cargarDatos();
      return { ok: true, mensaje: 'Salida registrada. La celda quedó libre.', dato: cerrado };
    } catch (err: any) {
      const mensaje = err?.error?.message || err?.error?.detail || 'No fue posible registrar la salida.';
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
        mensaje: err?.error?.message || err?.error?.detail || 'No fue posible cargar el reporte.',
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
    const tipo: TipoVehiculo = registro.celda.startsWith('M') ? 'MOTO' : 'CARRO';
    return this.celdas().filter((c) => c.estado === 'LIBRE' && c.tipoVehiculo === tipo);
  }

  async corregirCelda(idRegistro: number, codigoNuevo: string): Promise<Resultado<CorreccionAuditoria>> {
    const registro = this.registros().find((r) => r.id === idRegistro && !r.salida);
    if (!registro) {
      return { ok: false, mensaje: 'No se encontró la permanencia abierta a corregir.' };
    }
    const anterior = registro.celda;
    const nueva = codigoNuevo.trim().toUpperCase();
    if (nueva === anterior) {
      return { ok: false, mensaje: 'La nueva celda debe ser diferente a la actual.' };
    }

    try {
      const res = await firstValueFrom(
        this.http.patch<ApiCorreccionResponse>(
          `${this.baseUrl}/movimientos/${idRegistro}/celda`,
          {
            celda: nueva,
            operario_id: OPERARIO_ID,
          }
        )
      );

      const auditoria: CorreccionAuditoria = {
        idRegistro: res.movimiento_id,
        placa: registro.placa,
        celdaAnterior: res.celda_anterior,
        celdaNueva: res.celda_nueva,
        operario: OPERARIO_NOMBRE,
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
      const mensaje = err?.error?.message || 'No fue posible corregir la celda.';
      return { ok: false, mensaje };
    }
  }
}
