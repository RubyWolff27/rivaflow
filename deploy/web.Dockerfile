# Production web image — build the Vite SPA, serve static via Caddy.
# Build context = git root so we can reach both web/ and deploy/.
FROM node:20-slim AS build
WORKDIR /app
COPY web/package*.json ./
RUN npm ci || npm install
COPY web/ .
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY deploy/Caddyfile /etc/caddy/Caddyfile
EXPOSE 80
