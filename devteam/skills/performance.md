# SKILL: Performance — budgets, not guesswork

## Measure before optimizing. Optimizing without measuring is guessing, and it usually makes things worse.

### Budgets (concrete targets)
- API: p95 < 300ms on read endpoints, < 800ms on writes (adjust per case).
- Web frontend: LCP < 2.5s, INP < 200ms, CLS < 0.1 (Core Web Vitals).
- A page/endpoint that misses these is a defect, not "a future improvement".

### Backend
- The #1 killer is the database: N+1, missing index, query without a limit.
  ALWAYS review an endpoint's queries before considering it done.
- Cache where the data is stable and expensive to compute — WITH clear
  invalidation (without invalidation, a cache is a deferred bug).
- Pagination is mandatory on lists; never return "all the records".
- Heavy work (emails, images, exports) → queue/worker, not in the request.

### Frontend
- Don't block render on data: skeleton + progressive loading.
- Lazy-load routes/images; don't load what isn't visible.
- Avoid re-renders: memoize the expensive parts, don't do work on every render.
- Bundle: watch the size; import only what you use (real tree-shaking).

### Golden rule
Optimize the measured hot path, not the one that "seems" slow. An improvement
without a before/after metric is not accepted — it might change nothing or make
things worse.
