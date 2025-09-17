mod api;
mod auth;
mod cache;
mod config;
mod error;
mod middleware;
mod models;
mod repositories;
mod services;

use anyhow::{Ok, Result};
use axum::{Router, routing::get};
use bb8_redis::RedisConnectionManager;
use prometheus::{IntCounterVec, Registry, opts};
use std::net::SocketAddr;
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use crate::{
    auth::{JwtValidator, jwks::JwksManager, middleware::jwt_middleware},
    cache::{EventPublisher, UserCache},
    config::{ApiState, AppState, Config, HealthState, MetricsState},
    repositories::{ContactRepository, UserRepository},
    services::{ContactService, UserService},
};

#[tokio::main]
async fn main() {
    dotenvy::dotenv().ok();
    // Load configuration from environment
    let config = Config::from_env().unwrap();

    // Initialize logging/tracing
    init_tracing();

    info!("Starting User Service...");

    info!("Configuration loaded successfully");

    // Initialize database connection pool
    let db_pool = init_database(&config.database_url)
        .await
        .expect("Failed to connect to database");

    info!("Database connection established");

    // Initialize Redis connection
    let redis_client = init_redis(&config.redis_url)
        .await
        .expect("Failed to connect to Redis");

    info!("Redis connection established");

    let jwks_manager = init_jwk_manager(config.clone()).await.unwrap();

    // Initialize JWT validator with the JWKS manager
    let jwt_validator = JwtValidator::new(jwks_manager.clone());

    info!("JWT validator initialized");

    // Cache layer - talks to Redis
    let user_cache = UserCache::new(redis_client.clone());

    // Repository layer - talks to PostgreSQL
    let user_repository = UserRepository::new(db_pool.clone(), user_cache.clone());

    // Event publisher - publishes to Redis Pub/Sub
    let event_publisher = EventPublisher::new(redis_client.clone());

    let user_service = UserService::new(user_repository, user_cache, event_publisher);

    let contact_repository = ContactRepository::new(db_pool.clone());

    let contact_service = ContactService::new(contact_repository);

    // Build API State
    let api_state = ApiState::new(user_service, contact_service);

    // Build Metrics State
    let registry = Registry::new();
    let http_requests = IntCounterVec::new(
        opts!("http_requests_total", "Number of HTTP requests received"),
        &["method", "path", "endpoint"],
    )
    .unwrap();
    registry.register(Box::new(http_requests.clone())).unwrap();

    let metrics_state = MetricsState::new(registry, http_requests);

    // Build Health State
    let health_state = HealthState::new(db_pool, redis_client, jwks_manager.clone());

    // Build App State
    let app_state = AppState::new(api_state, health_state, metrics_state);

    info!("All services initialized successfully");

    // 8. Build the HTTP application
    let app = create_app(app_state, jwt_validator);

    // 9. Start the server
    let addr = SocketAddr::from(([0, 0, 0, 0], config.service_port));
    info!("User service listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("Failed to bind to address");

    axum::serve(listener, app)
        .await
        .expect("Server failed to run");
}

fn init_tracing() {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::from_default_env())
        .with(tracing_subscriber::fmt::layer())
        .init();
}

async fn init_database(database_url: &str) -> Result<sqlx::PgPool> {
    use sqlx::postgres::PgPoolOptions;

    let db_pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(database_url)
        .await?;

    Ok(db_pool)
}

pub async fn init_redis(redis_url: &str) -> Result<bb8::Pool<RedisConnectionManager>> {
    let manager = bb8_redis::RedisConnectionManager::new(redis_url)?;
    let pool = bb8::Pool::builder().max_size(15).build(manager).await?;

    Ok(pool)
}

pub async fn init_jwk_manager(config: Config) -> Result<JwksManager> {
    let openid_url = format!(
        "{}/realms/{}/.well-known/openid-configuration",
        &config.keycloak_url, &config.keycloak_realm
    );

    let http_client = reqwest::blocking::Client::builder().build()?;

    let response_json: serde_json::Value = http_client.get(openid_url).send()?.json().unwrap();

    let jwks_url = response_json.get("jwks_uri").unwrap().as_str().unwrap();

    info!("Connecting to JWKS URI: {}", jwks_url);

    let jwks_manager = JwksManager::new(jwks_url.to_string());
    Ok(jwks_manager)
}

fn create_app(app_state: AppState, jwt_validator: JwtValidator) -> Router {
    // Create protected routes (with auth)
    let protected_routes = Router::new()
        .nest("/api/v1/users", api::user::routes())
        .nest("/api/v1/contacts", api::contact::routes())
        // Apply JWT middleware to all protected routes once
        .layer(axum::middleware::from_fn_with_state(
            jwt_validator,
            jwt_middleware,
        ));

    let internal_routes = Router::new().nest("/internal/users", api::internal::user::routes());

    // Combine public + protected routes
    Router::new()
        // Public routes (no auth)
        .route("/metrics", get(api::metrics::metrics_handler))
        .route("/healthz", get(api::kubernetes::health_check))
        .route("/readyz", get(api::kubernetes::ready_check))
        // Protected routes (with auth)
        .merge(protected_routes)
        // Internal routes
        .merge(internal_routes)
        // Apply state
        .with_state(app_state.clone())
        // Global middleware (applied to all routes)
        .layer(axum::middleware::from_fn_with_state(
            app_state.metrics_state.clone(),
            middleware::metrics_middleware,
        ))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
}
