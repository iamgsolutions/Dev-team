# SKILL: Rendimiento — presupuestos, no adivinanzas

## Mide antes de optimizar. Optimizar sin medir es adivinar y suele empeorar.

### Presupuestos (objetivos concretos)
- API: p95 < 300ms en endpoints de lectura, < 800ms en escritura (ajusta por caso).
- Frontend web: LCP < 2.5s, INP < 200ms, CLS < 0.1 (Core Web Vitals).
- Una página/endpoint que los incumple es un defecto, no "una mejora futura".

### Backend
- El asesino #1 es la base de datos: N+1, falta de índice, query sin límite.
  Revisa SIEMPRE las queries de un endpoint nuevo antes de darlo por hecho.
- Caché donde el dato es estable y caro de calcular — CON invalidación clara
  (sin invalidación, la caché es un bug en diferido).
- Paginación obligatoria en listas; nunca devuelvas "todos los registros".
- Trabajo pesado (emails, imágenes, exports) → cola/worker, no en el request.

### Frontend
- No bloquees el render con datos: skeleton + carga progresiva.
- Lazy-load de rutas/imágenes; no cargues lo que no se ve.
- Evita re-renders: memoiza lo caro, no metas trabajo en cada render.
- Bundle: vigila el tamaño; importa solo lo que usas (tree-shaking real).

### Regla de oro
Optimiza el camino caliente medido, no el que "parece" lento. Una mejora sin
una métrica antes/después no se acepta — podría no cambiar nada o empeorar.
