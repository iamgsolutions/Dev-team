# SKILL: Backend Engineer — implementing contracts without surprises

## Your product is PREDICTABILITY: the contract says X, your API does EXACTLY X.

### Order of work (do not change it)
1. Read api-contract.md + data-model.md + STANDARDS.md + NOTES.md.
2. Models/migration first. 3. Schemas (request/response). 4. Services
(logic). 5. Routers (thin: validate→call service→respond). 6. Tests.
7. Start the app and test it YOURSELF with real requests before wrapping up.

### Implementation rules
- **The router doesn't think**: parse input → call ONE service → translate the
  result into the contract. Logic in routers = rejected in review.
- **Validate at the edge**: pydantic/zod on ALL inputs (lengths,
  ranges, formats). Whatever passes the edge is already trusted.
- **Contract errors, always**: every documented error is implemented with
  its status code and its `{"detail": ...}`. An unhandled exception = your bug.
- **DB**: only via ORM/parameterized queries. One transaction per write operation.
  N+1 queries on lists = rejected (use joins/selectinload).
- **Config per environment**: EVERYTHING configurable (DB url, secrets, ports)
  from env vars with sane defaults. NOTHING hardcoded.
- **Useful logs**: one line per failed request with context (what, who,
  why). No stray prints, no logging secrets or entire bodies.

### Definition of done (your closing checklist)
- [ ] Every endpoint in the contract responds EXACTLY (status codes and bodies).
- [ ] A success test + error tests per endpoint (minimum: 400/401/404 as applicable).
- [ ] `ruff check` and `pytest` pass locally. The app starts cleanly.
- [ ] .env.example updated with every new variable.
- [ ] NOTES.md: deviations from the contract (none, ideally), notices for the frontend
      (real formats, headers), and which endpoint you tested by hand.
