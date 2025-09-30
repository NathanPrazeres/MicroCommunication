# FROM rust:1.90 AS builder
#
# WORKDIR /app
#
# # Copy manifests first
# COPY Cargo.toml Cargo.lock ./
#
# # Pre-build dependencies
# RUN mkdir src && echo "fn main() {}" > src/main.rs
# RUN cargo build --release || true
# RUN rm -f src/main.rs
#
# # Copy actual source
# COPY src ./src
#
# # Build actual binary
# RUN cargo build --release
#
# # Runtime
# FROM debian:bookworm-slim
#
# RUN apt-get update \
#     && apt-get install -y debian-archive-keyring \
#     && apt-get update \
#     && apt-get install -y ca-certificates curl \
#     && rm -rf /var/lib/apt/lists/*
#
# WORKDIR /app
# COPY --from=builder /app/target/release/user-service /app/user-service
#
# EXPOSE 3000
#
# CMD ["./user-service"]


# =========================
# 1. Build Stage
# =========================
FROM rust:1.90 AS builder

WORKDIR /app

# Copy everything
COPY . .

# Build in release mode
RUN cargo build --release


# =========================
# 2. Runtime Stage
# =========================
FROM debian:bookworm-slim

# Install minimal runtime deps
RUN apt-get update && \
    apt-get install -y ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/release/user-service /usr/local/bin/user-service

# Environment Variables
ENV DATABASE_URL=postgres://admin:admin@postgres:5432/user_service

ENV REDIS_URL=redis://redis:6379
ENV REDIS_TTL_SECONDS=3600
ENV REDIS_CACHE_ENABLED=true

ENV KEYCLOAK_URL=http://keycloak:8080
ENV KEYCLOAK_REALM=app

ENV SERVICE_PORT=3000

ENV RUST_LOG=info
ENV RUST_BACKTRACE=1

ENV SQLX_OFFLINE=true

ENV ENVIRONMENT=production

EXPOSE 3000

CMD ["user-service"]
