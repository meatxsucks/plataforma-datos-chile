CREATE SCHEMA IF NOT EXISTS monitoreo;

CREATE TABLE IF NOT EXISTS monitoreo.chequeos (
    chequeo_id   SERIAL PRIMARY KEY,
    ejecutado_en TIMESTAMP NOT NULL DEFAULT now(),
    chequeo      VARCHAR(50) NOT NULL,
    mes          CHAR(7) NOT NULL,
    estado       VARCHAR(10) NOT NULL CHECK (estado IN ('ok', 'falla')),
    valor        NUMERIC(20,2),
    esperado     VARCHAR(100),
    detalle      TEXT
);
CREATE INDEX IF NOT EXISTS ix_chequeos_mes ON monitoreo.chequeos (chequeo, mes, ejecutado_en);

CREATE TABLE IF NOT EXISTS monitoreo.alertas (
    alerta_id    SERIAL PRIMARY KEY,
    creada_en    TIMESTAMP NOT NULL DEFAULT now(),
    chequeo_id   INTEGER NOT NULL REFERENCES monitoreo.chequeos (chequeo_id),
    mensaje      TEXT NOT NULL,
    explicacion  TEXT
);

GRANT USAGE ON SCHEMA monitoreo TO pdc_lector;
GRANT SELECT ON ALL TABLES IN SCHEMA monitoreo TO pdc_lector;
ALTER DEFAULT PRIVILEGES IN SCHEMA monitoreo GRANT SELECT ON TABLES TO pdc_lector;
