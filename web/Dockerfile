FROM oven/bun:1 AS deps
WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

FROM oven/bun:1 AS builder
WORKDIR /app

ARG NEXT_PUBLIC_BASE_PATH=""
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH}

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN bun run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app

ARG NEXT_PUBLIC_BASE_PATH=""
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
ENV CRIMS_DATA_DIR=/data/derived
ENV NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH}

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "const base=(process.env.NEXT_PUBLIC_BASE_PATH||'').replace(/\\/+$/,''); fetch('http://127.0.0.1:3000' + base + '/health').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
