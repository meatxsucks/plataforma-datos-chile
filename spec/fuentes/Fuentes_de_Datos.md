# Fuentes de datos

Revisadas el 2026-09-28. Las credenciales van en `.env`, nunca en el repo.

| Fuente | Acceso | Límite / condición | Dominio |
|---|---|---|---|
| Mercado Público — licitaciones y órdenes de compra | Ticket gratuito por correo, se pide con nombre, RUT y correo en `api.mercadopublico.cl` | 10.000 solicitudes diarias por ticket; volumen alto en horario 22:00–07:00. El listado por fecha trae solo código, nombre y estado: el detalle exige una consulta por orden (~1.300 al día). Responde 429 si se consulta rápido: se usa pausa de 2 s y espera de 60 s ante 429. Uso abusivo puede suspender el ticket | [[Compras_Publicas]] |
| Mercado Público — descargas masivas | `datos-abiertos.chilecompra.cl`: archivos .7z con CSV de órdenes de compra y licitaciones por mes | Para el histórico (backfill); la API queda para el incremental diario | [[Compras_Publicas]] |
| InfoLobby | Datos abiertos descargables y endpoint SPARQL (`datos.infolobby.cl/sparql`) | Por confirmar | [[Compras_Publicas]] |
| GTFS estático Red | Público | — | [[Transporte_Tiempo_Real]] |
| Posiciones GPS de buses (Web Service de Posicionamiento, actualiza cada 1 min) | Formulario Word del DTPM (`dtpm.cl/archivos/Formulario-26.docx`) enviado a `dys@dtpm.gob.cl`, indicando el uso de los datos | Respuesta en 10 días hábiles; credenciales de desarrollo por 2 meses; producción exige registrar IP pública | [[Transporte_Tiempo_Real]] |
| Banco Central — API BDE | Registro con correo en la BDE y activación de credenciales en el sitio de la API | 5 consultas por segundo por cuenta | [[Economia_Regional]] |
| CMF — UF y dólar | API key gratuita | Por confirmar | [[Economia_Regional]] |
| INE — empleo regional | Descargas públicas | — | [[Economia_Regional]] |

## Endpoints conocidos

- Mercado Público: `https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json` y
  `.../ordenesdecompra.json`, parámetros `fecha` (ddmmaaaa), `estado`, `codigo`, `CodigoOrganismo`,
  `CodigoProveedor`, `ticket`.
- Banco Central: `https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?function=GetSeries&timeseries=...&firstdate=...&lastdate=...`
  (usuario y clave de la API como parámetros).
