# Economía regional — transformación analítica y visualización

## Pregunta

¿Cómo se mueven el empleo y los precios en cada región frente al agregado nacional, y qué regiones
se adelantan o se atrasan al ciclo?

## Fuentes

- Banco Central (API BDE): IPC, IMACEC, tipo de cambio, series regionales.
- CMF: UF y dólar diarios.
- INE: empleo y desocupación regional (descargas).

Ver [[Fuentes_de_Datos]].

## Transformaciones

- Homologar frecuencias: diarias, mensuales y trimestrales en un calendario común.
- Deflactar montos nominales con IPC, lo que conecta con los montos de [[Compras_Publicas]].
- Desestacionalizar con STL y separar tendencia, estacionalidad y residuo.
- Correlación con rezago entre cada región y el agregado nacional para detectar adelantos y atrasos.
- Índice compuesto regional (z-scores ponderados) con metodología documentada.

## Visualización

Tablero con:
- mapa de Chile por región (desocupación, variación anual);
- series con tendencia y estacionalidad separadas;
- matriz de rezagos región contra país;
- cruce con compras públicas deflactadas por región.

Herramienta: Streamlit (código abierto, Apache 2.0).
