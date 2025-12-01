FROM node:20-slim AS base

# Don't set NODE_ENV=production in build stage (needs devDependencies)
ENV NEXT_TELEMETRY_DISABLED=1

# Accept build arguments for API URL (NEXT_PUBLIC_* vars must be set at build time)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG BACKEND_INTERNAL_URL
ARG ENVIRONMENT=production

# Set as environment variables for the build
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV BACKEND_INTERNAL_URL=${BACKEND_INTERNAL_URL}
ENV ENVIRONMENT=${ENVIRONMENT}

WORKDIR /app

# Install dependencies (including devDependencies for build)
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

# Build
COPY . .
RUN npm run build

# Final runtime image (use standalone output for smaller image)
FROM node:20-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Copy standalone build output
# Next.js standalone includes server.js and minimal node_modules
COPY --from=base /app/public ./public
COPY --from=base /app/.next/standalone ./
COPY --from=base /app/.next/static ./.next/static

# Copy package.json for runtime (standalone may need it for some operations)
COPY --from=base /app/package.json ./package.json

# Cloud Run sets PORT env var automatically
EXPOSE 3000

# Use PORT environment variable (Cloud Run provides this, default to 3000)
# Next.js standalone server.js uses PORT env var automatically
CMD sh -c "PORT=${PORT:-3000} node server.js"



