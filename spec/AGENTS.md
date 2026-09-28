# Protocolo de trabajo

## Al iniciar

1. Leer [[README]] y esta nota.
2. Revisar [[TODO]] para ubicar la fase en curso.
3. Revisar [[DUDAS]] por si la tarea depende de una decisión abierta.
4. Si la tarea toca un dominio, leer su nota en `dominios/`.

## Durante

- Cada cambio aplicado se registra en [[CHANGELOG]] en cuanto queda aplicado, no al cerrar.
- Una decisión de arquitectura nueva genera un ADR en `decisiones/`.
- Lo detectado y no hecho va a [[TODO]] cuando se detecta.

## Reglas

- Proyecto de aprendizaje: cada pieza nueva se explica en su nota (qué hace, por qué así, qué alternativa se descartó).
- No se copia código, nombres de buckets, tablas, jobs ni SQL de proyectos laborales. Se replican patrones, escritos desde cero.
- Todo en español.
- No commit ni push sin pedido explícito. Sin menciones a IA en commits ni en el código.
- Nada se ejecuta contra AWS real: todo apunta a floci (`http://localhost:4566`).
- Credenciales (tickets, usuarios de APIs) van en `.env`, nunca en el repo ni en el vault.
- No decir "funciona" sin haberlo corrido; cada fase tiene su criterio de término en [[TODO]].
- Comentarios de código pocos y como etiqueta; docstrings de una frase.
