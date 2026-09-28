# ADR-005 — IA para explicar alertas con OpenRouter

**Estado:** propuesta · **Fecha:** 2026-09-28

## Contexto

Las alertas de monitoreo dicen qué falló, pero no por qué ni qué revisar. Se quiere un uso acotado de IA que aporte sin volverse el centro del proyecto.

## Decisión

Una Lambda de alertas arma el contexto de la falla (proceso, tabla, volumen esperado contra obtenido, último error, linaje aguas arriba) y pide a un modelo gratuito de OpenRouter (sufijo `:free`) un resumen y una hipótesis de causa. El mensaje final lleva los datos duros más la explicación, marcada como generada.

## Límites del plan gratuito (docs de OpenRouter, 2026-09-28)

- 20 consultas por minuto; 50 por día sin compras, 1000 por día tras haber cargado 10 USD alguna vez.
- MCP oficial remoto: `https://mcp.openrouter.ai/mcp`.

## Consecuencias

- La alerta nunca depende del modelo: si OpenRouter falla o se agota la cuota, se envía la alerta sin explicación.
- No se envían datos personales al modelo, solo metadatos del proceso.
- La API key va en `.env`.
