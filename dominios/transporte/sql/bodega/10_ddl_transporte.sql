CREATE SCHEMA IF NOT EXISTS stage;
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS stage.deco (
    codigo_usuario VARCHAR(20),
    codigo_mtt     VARCHAR(20),
    codigo_ruta    VARCHAR(40),
    servicio_deco  VARCHAR(40),
    tipo_servicio  VARCHAR(20),
    cli_dsc        VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dw.dim_servicio (
    codigo_usuario VARCHAR(20) PRIMARY KEY,
    codigo_mtt     VARCHAR(20),
    servicio_deco  VARCHAR(40),
    tipo_servicio  VARCHAR(20),
    unidad         VARCHAR(100),
    actualizado_en TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dw.dim_recorrido (
    codigo_ruta    VARCHAR(40) PRIMARY KEY,
    codigo_usuario VARCHAR(20) NOT NULL REFERENCES dw.dim_servicio (codigo_usuario),
    sentido        CHAR(1) CHECK (sentido IN ('I', 'R')),
    actualizado_en TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_dim_recorrido_servicio ON dw.dim_recorrido (codigo_usuario);

GRANT USAGE ON SCHEMA dw TO pdc_lector;
GRANT SELECT ON dw.dim_servicio, dw.dim_recorrido TO pdc_lector;
