# Deployment References

Production deployment assets live in:

- `../docker/Dockerfile` — Backend container image
- `../docker/docker-compose.yml` — Full stack (backend + nginx frontend)
- `../docker/nginx.conf` — Reverse proxy configuration
- `../docs/DEPLOYMENT.md` — Step-by-step deployment guide
- `../.github/workflows/ci.yml` — CI pipeline

Run from repository root:

```bash
cd docker
docker compose up --build -d
```
