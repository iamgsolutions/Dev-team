# SKILL: Base de datos — esquemas y consultas que aguantan producción

### Diseño de esquema
- Normaliza hasta 3NF; desnormaliza solo con motivo medido (no "por si acaso").
- Toda tabla: PK explícita (UUID o bigint autoinc, UNO en todo el proyecto),
  `created_at`/`updated_at` timezone-aware.
- Claves foráneas con `ON DELETE` explícito (CASCADE/SET NULL/RESTRICT — decide,
  no dejes el default). Constraints de unicidad y CHECK para invariantes.
- Índices: en TODA FK, en columnas de filtros/orden frecuentes, y compuestos
  para queries reales. No indexes "por si acaso" (ralentizan escrituras).

### Migraciones
- Reversibles (up/down) y pequeñas. Una migración = un cambio lógico.
- Compatibles hacia atrás cuando hay deploy sin downtime: añade columna nullable
  → backfill → impón NOT NULL en una migración posterior. Nunca renombres/borres
  en el mismo paso que el código que aún usa el nombre viejo.
- Idempotentes en lo posible; nunca dependas de datos concretos de producción.

### Consultas
- **Mata el N+1**: en listas, carga relaciones con join/selectin, no en bucle.
- Paginación por keyset (cursor) para tablas grandes; offset solo en tablas chicas.
- Transacciones para operaciones multi-escritura; el nivel de aislamiento por
  defecto del motor salvo razón concreta. Bloqueos cortos.
- Nunca SQL por concatenación (inyección) — parametrizado/ORM siempre.
- Mide: una query en un endpoint caliente con `EXPLAIN` si dudas del plan.

### Datos
- Migraciones de datos separadas de las de esquema.
- Seeds realistas y coherentes para demo/test (no "asdf").
- Borrado: soft-delete (`deleted_at`) si hay que auditar o recuperar; hard-delete
  para datos personales que el usuario pide eliminar (GDPR).
