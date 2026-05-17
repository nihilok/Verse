# Verse — Claude Code Guide

## Deployment

Production runs on **pi5** (`ssh pi5`) at `~/Applications/Verse/`.

```bash
# On pi5 — deploy.sh handles the build and restart
cd ~/Applications/Verse && git pull && bash deploy.sh
```

`deploy.sh` prefixes Docker Compose with `DOCKER_API_VERSION=1.41` because the pi5 Docker Engine (20.10) tops out at API 1.41, while Compose v5 defaults to 1.52.

Production compose file: `docker-compose.prod.yml` (not `docker-compose.yml`).

## Pre-commit hooks

The project runs **prettier, eslint, ruff, and ruff-format** as pre-commit hooks.

**Prettier auto-modifies files** — if it fires, the commit will fail and the file will be changed on disk. Re-stage the modified file and commit again. This is expected behaviour, not an error.

Ruff line length is **110 characters**.

## React Context — useCallback is mandatory

Any function exposed through a React context that might be consumed in a `useEffect` dependency array **must be wrapped in `useCallback`**. Without it, the function gets a new reference on every render, causing infinite re-render loops (React error #185 in production).

This burned us once: `openModal` in `ModalContext` was not memoized → first-time visitors (who triggered `useLandingModal`) hit an infinite loop → white screen in production. All four functions in `ModalContext` (`openModal`, `closeModal`, `closeAllModals`, `isModalOpen`) are now wrapped in `useCallback`.

Enforce this pattern for any future context that exposes functions.

## Local dev

```bash
# Frontend (from frontend/)
bun run dev

# Full stack (from repo root)
docker compose up
```

The local `docker-compose.yml` maps Postgres to port `5432`. If that conflicts locally, change to `54321:5432` — but don't commit that change (prod uses a separate file).
