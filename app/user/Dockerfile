FROM rust:1.90 AS builder

WORKDIR /app

# Copy manifests first
COPY Cargo.toml Cargo.lock ./

# Pre-build dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release || true
RUN rm -f src/main.rs

# Copy actual source
COPY src ./src

# Build actual binary
RUN cargo build --release

# Runtime
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y debian-archive-keyring \
    && apt-get update \
    && apt-get install -y ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/target/release/user-service /app/user-service

EXPOSE 3000

CMD ["./user-service"]
