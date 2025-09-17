use axum::{
    extract::{Request, State},
    middleware::Next,
    response::Response,
};
use tracing::info;

use crate::{config::MetricsState, error::AppError};

pub async fn metrics_middleware(
    State(metrics): State<MetricsState>,
    request: Request,
    next: Next,
) -> Result<Response, AppError> {
    let method = request.method().clone();
    let path = request.uri().path().to_string();

    info!("New request [{}, {}]", method, path);

    let response = next.run(request).await;
    let status = response.status().as_u16().to_string();

    metrics
        .http_requests
        .with_label_values(&[method.as_str(), &path, &status])
        .inc();

    Ok(response)
}
