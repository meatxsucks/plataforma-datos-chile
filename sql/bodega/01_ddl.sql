CREATE SCHEMA IF NOT EXISTS stage;
CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dim_fecha (
    fecha_id     INTEGER PRIMARY KEY,
    fecha        DATE NOT NULL UNIQUE,
    anio         SMALLINT NOT NULL,
    trimestre    SMALLINT NOT NULL,
    mes          SMALLINT NOT NULL,
    anio_mes     CHAR(7) NOT NULL,
    dia          SMALLINT NOT NULL,
    dia_semana   SMALLINT NOT NULL,
    es_fin_semana BOOLEAN NOT NULL
);

INSERT INTO dw.dim_fecha
SELECT CAST(to_char(d, 'YYYYMMDD') AS INTEGER),
       d,
       EXTRACT(YEAR FROM d),
       EXTRACT(QUARTER FROM d),
       EXTRACT(MONTH FROM d),
       to_char(d, 'YYYY-MM'),
       EXTRACT(DAY FROM d),
       EXTRACT(ISODOW FROM d),
       EXTRACT(ISODOW FROM d) IN (6, 7)
FROM generate_series(DATE '2010-01-01', DATE '2030-12-31', INTERVAL '1 day') AS g(d)
ON CONFLICT (fecha_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS dw.dim_organismo (
    sk_organismo     SERIAL PRIMARY KEY,
    codigo_organismo VARCHAR(20) NOT NULL UNIQUE,
    nombre_organismo VARCHAR(300),
    sector           VARCHAR(100),
    actualizado_en   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dw.dim_unidad_compra (
    sk_unidad        SERIAL PRIMARY KEY,
    codigo_unidad    VARCHAR(20) NOT NULL UNIQUE,
    nombre_unidad    VARCHAR(300),
    rut_unidad       VARCHAR(20),
    region_unidad    VARCHAR(100),
    codigo_organismo VARCHAR(20),
    actualizado_en   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dw.dim_proveedor (
    sk_proveedor        SERIAL PRIMARY KEY,
    codigo_proveedor    VARCHAR(20) NOT NULL,
    rut_proveedor       VARCHAR(80),
    nombre_proveedor    VARCHAR(300),
    actividad_proveedor VARCHAR(300),
    region_proveedor    VARCHAR(100),
    es_persona_natural  BOOLEAN,
    vigente_desde       DATE NOT NULL,
    vigente_hasta       DATE NOT NULL DEFAULT DATE '9999-12-31',
    es_vigente          BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_proveedor_vigente ON dw.dim_proveedor (codigo_proveedor) WHERE es_vigente;

CREATE TABLE IF NOT EXISTS dw.fact_orden_compra (
    codigo             VARCHAR(40) NOT NULL,
    mes                CHAR(7) NOT NULL,
    sk_organismo       INTEGER REFERENCES dw.dim_organismo,
    sk_unidad          INTEGER REFERENCES dw.dim_unidad_compra,
    sk_proveedor       INTEGER REFERENCES dw.dim_proveedor,
    fecha_creacion_id  INTEGER REFERENCES dw.dim_fecha,
    fecha_envio_id     INTEGER REFERENCES dw.dim_fecha,
    tipo               VARCHAR(10),
    es_trato_directo   BOOLEAN,
    es_compra_agil     BOOLEAN,
    codigo_estado      INTEGER,
    codigo_licitacion  VARCHAR(40),
    moneda_oc          VARCHAR(10),
    monto_total_oc     NUMERIC(20,4),
    monto_total_oc_clp NUMERIC(20,4),
    total_neto_oc      NUMERIC(20,4),
    cantidad_items     INTEGER,
    PRIMARY KEY (codigo)
);
CREATE INDEX IF NOT EXISTS ix_fact_oc_mes ON dw.fact_orden_compra (mes);

CREATE TABLE IF NOT EXISTS dw.fact_orden_compra_item (
    id_item             BIGINT PRIMARY KEY,
    codigo              VARCHAR(40) NOT NULL,
    mes                 CHAR(7) NOT NULL,
    sk_organismo        INTEGER REFERENCES dw.dim_organismo,
    sk_proveedor        INTEGER REFERENCES dw.dim_proveedor,
    fecha_envio_id      INTEGER REFERENCES dw.dim_fecha,
    codigo_producto_onu VARCHAR(20),
    producto_generico   VARCHAR(300),
    rubro_n1            VARCHAR(300),
    rubro_n2            VARCHAR(300),
    rubro_n3            VARCHAR(300),
    cantidad            NUMERIC(20,4),
    unidad_medida       VARCHAR(50),
    moneda_item         VARCHAR(10),
    precio_neto         NUMERIC(20,4),
    total_linea_neto    NUMERIC(20,4)
);
CREATE INDEX IF NOT EXISTS ix_fact_item_mes ON dw.fact_orden_compra_item (mes);
