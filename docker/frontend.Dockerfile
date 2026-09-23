# Stage 1: Vite build with Node Alpine
FROM node:20-alpine3.19 AS build

WORKDIR /app/frontend

# Install only package manifests first — maximises Docker layer cache hits
COPY frontend/package.json frontend/package-lock.json* ./

# Use npm ci when lockfile is present for fully reproducible installs
RUN if [ -f package-lock.json ]; then \
      npm ci --no-audit --no-fund; \
    else \
      npm install --no-audit --no-fund; \
    fi \
    && npm cache clean --force

# Now copy full source tree (busts cache only when source changes)
COPY frontend/ .

# Build the Vite application (produces /app/frontend/dist)
RUN npm run build

# Stage 2: Minimal Nginx runtime — only built assets, no Node toolchain
FROM nginx:1.25-alpine3.19 AS runtime

# Copy ONLY built artifacts from the builder stage — no source leaks into runtime
COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY --from=build /app/frontend/legacy /usr/share/nginx/html/legacy

# Nginx site config
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Run as non-root nginx user (best practice)
RUN addgroup -S nginx || true \
    && adduser -S nginx -G nginx || true \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 80/tcp
