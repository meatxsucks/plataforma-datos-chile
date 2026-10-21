# DTPM — Web Services de posicionamiento y alertas

Acceso otorgado el 2026-10-21 por el DTPM (Directorio de Transporte Público Metropolitano). Credenciales de
desarrollo válidas por 2 meses (vencen cerca del **2026-12-21**); para producción hay que registrar una IP pública.
Credenciales en `.env` (`DTPM_USUARIO`, `DTPM_CLAVE`), nunca en el repo.

Documentación oficial en `docs/`:

- `docs/DyS Web Service Posicionamiento.pdf`
- `docs/DyS Web Service Alertas.pdf`
- `docs/DECO_VIGENTES_202607061152.csv` (diccionario de servicios)

## Acceso

| Servicio | URL | Autenticación | Tamaño por consulta |
|---|---|---|---|
| Posiciones | `http://www.dtpmetropolitano.cl/posiciones` | HTTP Basic | ~6,4 MB |
| Alertas | `http://www.dtpmetropolitano.cl/alertas` | HTTP Basic | ~0,5 MB |

- Ambos son HTTP sin TLS: las credenciales viajan sin cifrar.
- Los datos se actualizan cada 1 minuto. **No consultar con intervalos menores a 1 minuto**: el servicio responde el
  error `-104` ("No puede volver a ejecutar hasta pasados X segundos").
- El enrolamiento es por usuario + IP (error `-103` si la IP no está autorizada). En desarrollo funcionó desde la IP
  de la casa sin registrarla.

## Posiciones

Respuesta: `{"fecha_consulta": "AAAAMMDDhhmmss", "posiciones": ["...", ...]}`. Cada texto es un bus con sus últimas
1 a 4 transmisiones GPS, separadas por `;`, 12 campos por transmisión y un `;` final.

| # | Campo | Tipo | Nota |
|---|---|---|---|
| 0 | Fecha hora GPS | `dd-mm-aaaa hh:mm:ss` | **UTC** |
| 1 | Patente | texto | `BJFC-73`, `VX-2321` |
| 2 | Latitud | decimal | WGS 84 (EPSG:4326) |
| 3 | Longitud | decimal | WGS 84 |
| 4 | Velocidad | decimal | km/h, 1 decimal |
| 5 | Dirección | entero | 0 N, 1 NE, 2 E, 3 SE, 4 S, 5 SO, 6 O, 7 NO |
| 6 | Operador | entero | identificador del concesionario |
| 7 | Servicio | texto | código del sinóptico (`T502`); no siempre es el que ve el público: traducir con el archivo DECO |
| 8 | Sentido | texto | `I` ida, `R` retorno, vacío sin sentido |
| 9 | Ruta en consola | texto | `T201 00I` |
| 10 | Ruta en sinóptico | texto | `T201 03I` |
| 11 | Fecha hora de inserción | `dd-mm-aaaa hh:mm:ss` | UTC, cuando entró a la base del DTPM |

Cuidado: `fecha_consulta` viene en **hora de Chile** y las fechas GPS en **UTC**.

### Perfil de la consulta del 2026-10-21 20:05 (hora de Chile)

| Métrica | Valor |
|---|---|
| Buses en la respuesta | 13.946, todos con 4 transmisiones |
| Transmitieron en los últimos 5 min | 6.128 (44%) |
| Transmitieron en la última hora | 6.373 |
| Servicios distintos | 721 |
| Operadores | 20 (los 3 mayores: 4, 16 y 5, con ~2.000 buses cada uno) |

El resto son buses detenidos, fuera de servicio o con última transmisión antigua (hay casos de 2023): **filtrar por
antigüedad** antes de cualquier cálculo.

## Alertas

Respuesta: `{"estado": 1, "mensaje": "", "cantidadRegistros": N, "registros": [...]}`. Devuelve las alertas activas
al momento de la consulta. Clave única: **origen + id**.

| Campo | Nota |
|---|---|
| `origen` | `PST` alertas del operador, `MTT` alertas de sistema, `CNS` enviadas desde la consola del bus |
| `id`, `tipo` | ver tabla de tipos |
| `fecharegalerta`, `fechageneracion` | ISO 8601 en UTC |
| `latitud`, `longitud` | no vienen en alertas `CNS` |
| `objeto` | `BUS` o `SERVICIO` |
| `patente` | solo si el objeto es `BUS` |
| `datoalerta`, `vallimite` | valor que gatilla y umbral (minutos) |
| `criticidad` | solo `ALEBUSREGFUEPO` y `ALEBUSRETDESP` |
| `operador`, `servicio`, `sentido` | |
| `textoalerta`, `desccorta`, `descripcion` | textos; los campos nulos no se envían |

### Tipos de alerta

| Origen | Tipo | Significado |
|---|---|---|
| PST | Alerta-01 / 02 | Bus atrasado / adelantado respecto de su antecesor |
| PST | Alerta-03 | Bus detenido por tiempo excesivo |
| PST | Alerta-04 / 05 | Plazas en circulación altas / bajas |
| PST | Alerta-06 | Velocidad alta |
| PST | Alerta-07 | Salida lenta desde el cabezal |
| PST | Alerta-08 | Fuera de ruta |
| PST | Alerta-09 | Sin transmisión |
| PST | Alerta-10 | Sin bus virtual en asociación automática |
| MTT | ALEBUSCONTROL / PANNE / CONG / DESACT | Bus en control, en panne, en congestión, desactivado |
| MTT | ALEBUSREGFUEPO | Regularidad fuera del programa de operación |
| MTT | ALEBUSEXCVEL | Exceso de velocidad |
| MTT | ALEBUSFUERUTA | Fuera de ruta |
| MTT | ALEBUSRETDESP | Servicio-sentido con retraso en despacho |
| CNS | Bus en Panne, Desvío no Programado, Accidente TS, Vandalismo | Reportes del conductor (con detalle: frenos, neumáticos, Carabineros, feria, trabajos en la vía, agresiones, etc.) |

### Perfil de la consulta del 2026-10-21

1.006 alertas activas: 943 `MTT` y 63 `PST`. Por tipo: fuera de ruta (`ALEBUSFUERUTA`) 848, regularidad fuera de
programa 91, sin transmisión 23, detenido 16, fuera de ruta PST 9, velocidad alta 8.

### Códigos de error

| Código | Significado |
|---|---|
| -1 | Error interno |
| -100 | No se pudo verificar enrolamiento |
| -101 | Usuario no existe |
| -102 | Error de configuración del servicio |
| -103 | Usuario + IP no enrolado |
| -104 | Consulta antes del intervalo mínimo |

## Archivo DECO (`DECO_VIGENTES_202607061152.csv`)

Diccionario de servicios vigentes al 2026-07-06: 776 filas, separador `;`, UTF-8 (ASCII).

| Columna | Ejemplo | Uso |
|---|---|---|
| `CODIGO_USUARIO` | `B02N` | Código que ve el público |
| `CODIGO_MTT` | `902N` | Código del Ministerio de Transportes |
| `CODIGO_RUTA` | `T902 E3 00I` | Cruza con "ruta en consola/sinóptico" de las posiciones |
| `SERVICIO_DECO` | `902 E3` | Servicio interpretado |
| `TIPO_SERVICIO` | `DECO` | |
| `CLI_DSC` | `U9 - Omega US2` | Unidad de servicio y operador |

Es la dimensión que traduce el código interno del bus al recorrido público: va a la bodega como `dim_servicio`.

## Ideas para la fase de tiempo real

- **Mapa en vivo** (Streamlit + pydeck): buses activos en los últimos 5 minutos, coloreados por velocidad o por
  operador, con las alertas encima.
- **Velocidad comercial por corredor y hora**: con las 4 transmisiones de cada consulta ya se puede estimar la
  velocidad media sin depender de la velocidad instantánea.
- **Detección de "trenes de buses"** (bunching): buses del mismo servicio y sentido a menos de N metros; cruzar con
  `Alerta-01/02` para ver si el sistema ya lo detecta.
- **Ranking de operadores**: % de flota transmitiendo, alertas por cada 100 buses, fuera de ruta por servicio.
- **Mapa de calor de alertas** por comuna y franja horaria (fuera de ruta, panne, congestión).
- **Comparar con el GTFS programado**: frecuencia real vs. programada por servicio, que es la pregunta del dominio
  [[Transporte_Tiempo_Real]].

## Pendiente

- Productor que consulte posiciones y alertas cada 1 minuto (mínimo permitido) y publique en Kinesis.
- Cargar el archivo DECO como `dim_servicio`.
- Avisar al DTPM antes del vencimiento si se quiere seguir usando el servicio.
