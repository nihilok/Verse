FROM oven/bun:1 as build

WORKDIR /app

# Copy package files
COPY package.json bun.lockb* ./

# Install dependencies and explicitly add ARM64 Rollup support
RUN bun install && \
    bun add -D @rollup/rollup-linux-arm64-gnu

# Copy source code
COPY . .

# Build the application
RUN bun run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
