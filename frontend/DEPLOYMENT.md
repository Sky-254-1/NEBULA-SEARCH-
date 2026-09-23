# Nebula Search Frontend - Deployment Guide

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Update `VITE_API_URL` if your backend is not at `http://localhost:8000/api/v1`.

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

### 4. Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

### 5. Preview Production Build

```bash
npm run preview
```

## Production Deployment

### Build the Application

```bash
npm run build
```

### Deploy to Vercel

```bash
npm install -g vercel
vercel --prod
```

### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### Deploy with Docker

```bash
docker build -t nebula-frontend .
docker run -p 80:80 nebula-frontend
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_URL` | Backend API URL | Yes | `http://localhost:8000/api/v1` |
| `VITE_APP_NAME` | Application name | No | `Nebula Search` |
| `VITE_APP_VERSION` | Application version | No | `1.0.0` |

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Build and Run

```bash
docker build -t nebula-frontend .
docker run -p 80:80 nebula-frontend
```

## Performance Optimization

### Bundle Analysis

```bash
npm install -g rollup
npm run build
npx rollup-plugin-visualizer
```

### Lighthouse Audit

```bash
npm install -g lighthouse
lighthouse http://localhost:5173 --view
```

## Troubleshooting

### Common Issues

1. **Module not found errors**: Run `npm install` again
2. **TypeScript errors**: Run `npm run build` to see full error list
3. **API connection issues**: Check `VITE_API_URL` in `.env`
4. **PWA not installing**: Ensure HTTPS is enabled in production

### Clear Cache

```bash
npm run clean
rm -rf node_modules dist .vite
npm install
```

## Monitoring

### Error Tracking

Consider integrating:
- Sentry
- LogRocket
- Datadog

### Analytics

Consider integrating:
- Google Analytics
- Mixpanel
- Amplitude

## Security Checklist

- [ ] HTTPS enabled
- [ ] Security headers configured
- [ ] CSP headers set
- [ ] API URL uses HTTPS in production
- [ ] Environment variables secured
- [ ] Dependencies audited (`npm audit`)

## Support

For issues and questions, please refer to the main project documentation.