# Docker Compose configuration

The default Compose files do not publish PostgreSQL, Redis, or MinIO ports.
Production traffic enters through the Nginx edge on ports 80 and 443. The
backend is reachable by Nginx on the private Compose network; data services
are attached only to the internal network.

For local development, create an untracked `.env` file with local-only values:

```dotenv
POSTGRES_PASSWORD=replace-with-a-local-development-password
JWT_SECRET=replace-with-a-random-secret-at-least-32-characters-long
MINIO_ROOT_USER=nebula-local
MINIO_ROOT_PASSWORD=replace-with-a-local-development-minio-password
```

Then start the base stack with the explicit development override:

```sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

The override publishes development ports for the API, frontend, PostgreSQL,
Redis, and MinIO. Do not use those local credentials in production. Production
deployment requires explicit database, JWT, MinIO, and RabbitMQ secrets. Use
URL-safe characters in passwords interpolated into database or AMQP URLs, or
provide URL-encoded values. Keep `.env` out of version control and use the
deployment platform's secret store in production.
