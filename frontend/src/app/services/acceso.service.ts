import { Injectable, computed, signal } from '@angular/core';
import {
  Celda, Comprobante, ConsultaEntrada, CorreccionAuditoria, RegistroAcceso, Resultado, TipoComprobante, TipoVehiculo, Vehiculo,
} from '../models/models';

const OPERARIO = 'Diurno 1';
const horasAtras = (h: number): Date => new Date(Date.now() - h * 3_600_000);
const numero = (i: number): string => String(i + 1).padStart(2, '0');

const crearCeldas = (): Celda[] => [
  ...Array.from({ length: 70 }, (_, i): Celda => ({ codigo: `A-${numero(i)}`, tipoVehiculo: 'CARRO', estado: i === 0 ? 'OCUPADA' : 'LIBRE' })),
  ...Array.from({ length: 10 }, (_, i): Celda => ({ codigo: `M-${numero(i)}`, tipoVehiculo: 'MOTO', estado: 'LIBRE' })),
];

/**
 * Servicio con DATOS SIMULADOS, alineado con los mockups de Paul (HU-01 a HU-09).
 * Cuando el backend esté listo, solo cambia el interior de cada método por una llamada HttpClient.
 */
@Injectable({ providedIn: 'root' })
export class AccesoService {
  private readonly vehiculos: Vehiculo[] = [
    { placa: 'ABC123', tipo: 'CARRO', marca: 'Chevrolet Onix', color: 'Blanco', mensualidadFin: new Date(2026, 10, 21) },
    { placa: 'VEN001', tipo: 'CARRO', marca: 'Renault Logan', color: 'Rojo', mensualidadFin: new Date(2026, 8, 30) },
    { placa: 'INS001', tipo: 'CARRO', marca: 'Kia Rio', color: 'Azul', mensualidadFin: new Date(2026, 11, 31) },
    { placa: 'XYZ99A', tipo: 'MOTO', marca: 'Yamaha FZ', color: 'Negro', mensualidadFin: new Date(2026, 11, 15) },
  ];

  readonly celdas = signal<Celda[]>(crearCeldas());

  readonly registros = signal<RegistroAcceso[]>([
    {
      id: 1, placa: 'INS001', celda: 'A-01', entrada: horasAtras(30), operario: OPERARIO,
      comprobanteEntrada: { numero: 'AC-INS001-OPEN', tipo: 'ENTRADA', fechaEmision: horasAtras(30) },
    },
  ]);

  readonly correcciones = signal<CorreccionAuditoria[]>([]);

  readonly activos = computed(() => this.registros().filter((r) => !r.salida));
  readonly libres = computed(() => this.celdas().filter((c) => c.estado === 'LIBRE').length);
  readonly ocupadas = computed(() => this.celdas().filter((c) => c.estado === 'OCUPADA').length);

  private contadorSalidas = 0;

  normalizar(placa: string): string {
    return placa.trim().toUpperCase().replace(/\s+/g, '');
  }

  buscarVehiculo(placa: string): Vehiculo | undefined {
    return this.vehiculos.find((v) => v.placa === this.normalizar(placa));
  }

  /** Paso 1 de la entrada (HU-01, HU-03): consulta sin modificar nada. */
  consultarEntrada(placa: string): ConsultaEntrada {
    const v = this.vehiculos.find((x) => x.placa === this.normalizar(placa));
    if (!v) {
      return { estado: 'NO_REGISTRADO', mensaje: 'El vehículo no está registrado. No se permite el ingreso. No se modificó la ocupación.' };
    }
    const abierto = this.activos().find((r) => r.placa === v.placa);
    if (abierto) {
      return { estado: 'YA_DENTRO', vehiculo: v, celdaActual: abierto.celda, mensaje: 'Este vehículo ya tiene una permanencia abierta. No se puede registrar otra entrada.' };
    }
    if (v.mensualidadFin < new Date()) {
      return { estado: 'VENCIDA', vehiculo: v, mensaje: 'Mensualidad vencida. El vehículo no está autorizado para ingresar.' };
    }
    const delTipo = this.celdas().filter((c) => c.tipoVehiculo === v.tipo);
    if (!delTipo.some((c) => c.estado === 'LIBRE')) {
      const etiqueta = v.tipo === 'MOTO' ? 'motos' : 'automóviles';
      return { estado: 'SIN_CUPO', vehiculo: v, mensaje: `No hay celdas disponibles para este tipo de vehículo (${etiqueta} ${delTipo.length}/${delTipo.length}).` };
    }
    return { estado: 'AUTORIZADO', vehiculo: v, mensaje: '' };
  }

  /** Paso 2 (HU-02, HU-04): asigna celda y genera el comprobante. */
  confirmarEntrada(placa: string): Resultado<RegistroAcceso> {
    const c = this.consultarEntrada(placa);
    if (c.estado !== 'AUTORIZADO' || !c.vehiculo) return { ok: false, mensaje: c.mensaje };

    const celda = this.celdas().find((x) => x.estado === 'LIBRE' && x.tipoVehiculo === c.vehiculo!.tipo)!;
    const registro: RegistroAcceso = {
      id: this.registros().length + 1,
      placa: c.vehiculo.placa,
      celda: celda.codigo,
      entrada: new Date(),
      operario: OPERARIO,
      comprobanteEntrada: { numero: this.codigoComprobante(), tipo: 'ENTRADA', fechaEmision: new Date() },
    };
    this.registros.update((l) => [...l, registro]);
    this.cambiarEstadoCelda(celda.codigo, 'OCUPADA');
    return { ok: true, mensaje: 'Entrada registrada correctamente.', dato: registro };
  }

  /** Se ajusta en la Etapa 2 (salida por comprobante). */
  registrarSalida(placa: string): Resultado<RegistroAcceso> {
    const activo = this.activos().find((r) => r.placa === this.normalizar(placa));
    if (!activo) return { ok: false, mensaje: 'No hay un ingreso activo para esta placa.' };
    const cerrado: RegistroAcceso = {
      ...activo,
      salida: new Date(),
      comprobanteSalida: this.comprobanteSalida(),
    };
    this.registros.update((l) => l.map((r) => (r.id === activo.id ? cerrado : r)));
    this.cambiarEstadoCelda(activo.celda, 'LIBRE');
    return { ok: true, mensaje: 'Salida registrada. La celda quedó libre.', dato: cerrado };
  }

  permanencia(r: RegistroAcceso): string {
    const fin = r.salida ?? new Date();
    const min = Math.max(0, Math.round((fin.getTime() - r.entrada.getTime()) / 60_000));
    return `${Math.floor(min / 60)} h ${min % 60} min`;
  }

  private cambiarEstadoCelda(codigo: string, estado: Celda['estado']): void {
    this.celdas.update((l) => l.map((c) => (c.codigo === codigo ? { ...c, estado } : c)));
  }

  private codigoComprobante(): string {
    const letras = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    const bloque = () => Array.from({ length: 4 }, () => letras[Math.floor(Math.random() * letras.length)]).join('');
    return `AC-${bloque()}-${bloque()}`;
  }

  private comprobanteSalida(): Comprobante {
    this.contadorSalidas++;
    const tipo: TipoComprobante = 'SALIDA';
    return { numero: `SAL-${String(this.contadorSalidas).padStart(4, '0')}`, tipo, fechaEmision: new Date() };
  }

  /** HU-09: lista las celdas libres compatibles con el tipo del vehículo del registro. */
  celdasCompatibles(idRegistro: number): Celda[] {
    const registro = this.registros().find((r) => r.id === idRegistro && !r.salida);
    if (!registro) return [];
    const tipo: TipoVehiculo = registro.celda.startsWith('M') ? 'MOTO' : 'CARRO';
    return this.celdas().filter((c) => c.estado === 'LIBRE' && c.tipoVehiculo === tipo);
  }

  /** HU-09: corrige la celda de una permanencia abierta sin crear otro movimiento. */
  corregirCelda(idRegistro: number, codigoNuevo: string): Resultado<CorreccionAuditoria> {
    const registro = this.registros().find((r) => r.id === idRegistro && !r.salida);
    if (!registro) {
      return { ok: false, mensaje: 'No se encontró la permanencia abierta a corregir.' };
    }
    const anterior = registro.celda;
    const nueva = codigoNuevo.trim().toUpperCase();
    if (nueva === anterior) {
      return { ok: false, mensaje: 'La nueva celda debe ser diferente a la actual.' };
    }
    const destino = this.celdas().find((c) => c.codigo === nueva);
    if (!destino) {
      return { ok: false, mensaje: `La celda ${nueva} no existe.` };
    }
    const tipoActual: TipoVehiculo = anterior.startsWith('M') ? 'MOTO' : 'CARRO';
    if (destino.tipoVehiculo !== tipoActual) {
      return { ok: false, mensaje: `La celda ${nueva} no es compatible con el tipo del vehículo.` };
    }
    if (destino.estado !== 'LIBRE') {
      return { ok: false, mensaje: `La celda ${nueva} está ocupada y no puede recibir otra permanencia.` };
    }
    this.registros.update((l) => l.map((r) => (r.id === idRegistro ? { ...r, celda: nueva } : r)));
    this.cambiarEstadoCelda(anterior, 'LIBRE');
    this.cambiarEstadoCelda(nueva, 'OCUPADA');
    const auditoria: CorreccionAuditoria = {
      idRegistro,
      placa: registro.placa,
      celdaAnterior: anterior,
      celdaNueva: nueva,
      operario: OPERARIO,
      fecha: new Date(),
    };
    this.correcciones.update((l) => [...l, auditoria]);
    return { ok: true, mensaje: `Celda actualizada de ${anterior} a ${nueva}.`, dato: auditoria };
  }
}
