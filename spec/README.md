# Plataforma de Datos Chile

Plataforma de datos de punta a punta sobre datos públicos chilenos, construida sobre servicios de AWS
emulados localmente con [floci](https://github.com/floci-io/floci). El objetivo es aprender y mostrar
arquitectura de datos: ingesta batch y en tiempo real, capas raw/stg/analytics, bodega dimensional,
orquestación, APIs de datos, monitoreo y visualización.

## Tres dominios, un mismo motor

| Dominio | Rol en el proyecto | Pregunta que responde | Nota |
|---|---|---|---|
| Compras públicas | Principal (batch diario) | ¿Qué organismos concentran compras en pocos proveedores o en trato directo, y se cruza eso con audiencias de lobby? | [[Compras_Publicas]] |
| Transporte Santiago | Tiempo real (streaming) | ¿Cuánto se desvía el servicio real del programado, por recorrido y hora? | [[Transporte_Tiempo_Real]] |
| Economía regional | Transformación analítica + visualización | ¿Cómo se mueven empleo y precios por región frente al agregado nacional? | [[Economia_Regional]] |

## Mapa del vault

- [[AGENTS]] — protocolo de trabajo.
- [[ARQUITECTURA]] — vista general, capas, servicios y cómo se emula cada uno.
- [[TODO]] — fases y tareas, con criterio de término.
- [[CHANGELOG]] — registro de cambios aplicados.
- [[DUDAS]] — decisiones abiertas que bloquean o condicionan fases.
- `dominios/` — una nota por dominio: fuentes, modelo de datos, transformaciones, API.
- `decisiones/` — ADRs: una decisión por nota, con contexto, alternativas y consecuencias.
- `fuentes/` — [[Fuentes_de_Datos]]: acceso, límites y licencias de cada fuente.
- `aprendizaje/` — [[Patrones]] y [[Patron_Jobs_Glue]]: los patrones que el proyecto practica y por qué.
