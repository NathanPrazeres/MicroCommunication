use axum::{http::StatusCode, response::Json};
use serde_json::{Value, json};
use tracing::info;

pub async fn health_check() -> (StatusCode, Json<Value>) {
    info!("Returning StatusCode OK (200)...");
    (
        StatusCode::OK,
        Json(json!({
            "status": "healthy",
            "service": "user-service",
            "timestamp": chrono::Utc::now().to_rfc3339()
        })),
    )
}

pub async fn ready_check() -> (StatusCode, Json<Value>) {
    info!("Returning StatusCode OK (200)...");
    (
        StatusCode::OK,
        Json(json!({
            "status": "ready",
            "service": "user-service",
            "timestamp": chrono::Utc::now().to_rfc3339()
        })),
    )
}
