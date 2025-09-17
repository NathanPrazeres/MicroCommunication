use axum::{extract::State, response::IntoResponse};
use prometheus::{Encoder, TextEncoder};

use crate::config::MetricsState;

pub async fn metrics_handler(State(state): State<MetricsState>) -> impl IntoResponse {
    let encoder = TextEncoder::new();
    let metric_families = state.registry.gather();
    let mut buffer = Vec::new();
    encoder.encode(&metric_families, &mut buffer).unwrap();

    let content_type = encoder.format_type().to_string();

    ([(axum::http::header::CONTENT_TYPE, content_type)], buffer)
}
