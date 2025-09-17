use axum::{extract::State, http::StatusCode, response::Json};
use serde_json::{Value, json};
use std::time::Duration;
use tokio::time::timeout;

use crate::config::HealthState;

pub async fn health_check() -> (StatusCode, Json<Value>) {
    (
        StatusCode::OK,
        Json(json!({
            "status": "healthy",
            "service": "user-service",
            "timestamp": chrono::Utc::now().to_rfc3339()
        })),
    )
}

pub async fn ready_check(State(state): State<HealthState>) -> (StatusCode, Json<Value>) {
    let timeout_duration = Duration::from_secs(2);

    let db_ok = timeout(timeout_duration, state.db_pool.acquire())
        .await
        .ok()
        .and_then(|res| res.ok())
        .is_some();

    let redis_ok = timeout(timeout_duration, state.redis_pool.get())
        .await
        .ok()
        .and_then(|res| res.ok())
        .is_some();

    let jwks_ok = timeout(timeout_duration, state.jwks.refresh())
        .await
        .ok()
        .and_then(|res| res.ok())
        .is_some();

    (
        StatusCode::OK,
        Json(json!({
            "db": db_ok,
            "redis": redis_ok,
            "jwks": jwks_ok,
        })),
    )
}
