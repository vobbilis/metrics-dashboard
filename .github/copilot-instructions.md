# Metrics Dashboard — Copilot Instructions

A full-stack metrics dashboard (FastAPI backend + React/TypeScript frontend).
Testbed for GitHub Copilot coding agent workflows.

## Code Style

### Backend (Python 3.11+)
- **Ruff** for linting + formatting: `line-length = 100`, rules `["E", "F", "I", "UP"]`
- Type hints on all functions with explicit return annotations (see `backend/main.py` routes)
- **Pydantic v2** `BaseModel` — use `Field(...)` for required, `default_factory` for defaults
- Routes are plain `@app.get/post/delete` functions (no APIRouter abstraction)
- Errors: raise `HTTPException(status_code=..., detail=...)` — all errors use `{ detail: str }` shape
- POST endpoints return `status_code=201`
- DELETE returns `{"deleted": N}` even when N=0 — no 404 on missing

### Frontend (TypeScript strict)
- **TypeScript strict mode** with `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`
- Functional components only, named exports for components, default export for `App`
- Raw `fetch()` API client — no axios or query libraries (see `frontend/src/api.ts`)
- Base URL is `'/api'` — Vite proxy strips `/api` prefix before forwarding to backend
- CSS class-based styling (`.metric-card`, `.metric-grid`, etc.)
- Prettier as formatter (VS Code setting)

## Architecture

```
frontend (:5173)  ──/api/metrics──▶  Vite proxy  ──/metrics──▶  backend (:8000)
                                     (strips /api)              │
                                                          MetricStore (in-memory list)
```

- **Store is a module-level singleton** in `backend/main.py` — `store = MetricStore()`, no DI
- Store is a plain `list[MetricOut]` with no threading lock (intentional simplicity)
- Frontend polls `GET /metrics` every 5s via `setInterval` — no WebSocket
- No auth, no persistence, no rate limiting — local dev testbed only
- CORS allows only `http://localhost:5173`

## Build and Test

### Backend
```bash
cd backend
pip install -r requirements.txt        # fastapi 0.115.6, pydantic 2.10.3, uvicorn 0.32.1
uvicorn main:app --reload --port 8000   # dev server
pytest tests/ -v                        # sync TestClient tests, asyncio_mode=auto
ruff check .                            # lint
ruff format --check .                   # format check
```

### Frontend
```bash
cd frontend
npm install                # react 18, vite 6, vitest 2, typescript 5.6
npm run dev                # Vite dev server, port 5173, proxies /api → :8000
npm run build              # tsc --noEmit && vite build (typecheck built-in)
npm test                   # vitest (jsdom, globals, @testing-library)
npm run lint               # eslint --max-warnings 0
npm run typecheck          # tsc --noEmit
```

### CI (`.github/workflows/ci.yml`)
Backend: ruff check → ruff format --check → pytest.
Frontend: typecheck → lint → vitest --run → build.

## Project Conventions

### API contract
```
POST /metrics          { name: str, value: float, tags?: dict[str,str] } → 201
GET  /metrics          → [{ id, name, value, tags, timestamp }]
GET  /metrics/{name}   → [{ id, name, value, tags, timestamp }]  (404 if none)
DELETE /metrics/{name}  → { deleted: int }  (0 if none, no 404)
GET  /health           → { status: "ok" }
```

### Test patterns
- **Backend**: `TestClient(app)` at module level, `autouse` fixture calls `store.clear()`.
  Import store from `main` to clear between tests. No mocking — tests hit real routes.
- **Frontend**: `vi.mock('./api')` full module mock, `@testing-library/react` with
  `screen.findByText()` for async, `@testing-library/jest-dom` matchers.

### Agent workflow (`.github/agents/`)
- **builder** (Claude Sonnet 4): implements one task, runs tests/lint to verify
- **validator** (Claude Sonnet 4): read-only, inspects files, reports PASS/FAIL
- **PostToolUse hook** (`.github/hooks/`): auto-runs `ruff check` on `.py` writes,
  `npm run typecheck` on `.ts/.tsx` writes — blocks on failure

### Conventions
- Branch names: `feature/`, `fix/`, `chore/` prefixes
- Commits: conventional commits (`feat:`, `fix:`, `test:`, `chore:`)
- PRs must pass CI before merge
- Never commit `.env` files or API keys
- Plan specs in `specs/**/*.md` follow task format with IDs, dependencies, and builder→validator pairs

## Dependency Management

Dependencies are installed automatically at session start via `.github/hooks/setup.sh`.
You should never need to ask the user to install dependencies manually.

If a command fails with a missing module or package error, self-heal before retrying:

```bash
# Backend missing module
pip install -r backend/requirements.txt

# Frontend missing module
cd frontend && npm install
```

Never surface a missing dependency as a blocking error to the user.
Always attempt to install and retry first.
