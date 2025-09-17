use axum::extract::FromRef;
use prometheus::{IntCounterVec, Registry};

use crate::config::AppState;

#[derive(Debug, Clone)]
pub struct MetricsState {
    pub registry: Registry,
    pub http_requests: IntCounterVec,
}

impl MetricsState {
    pub fn new(registry: Registry, http_requests: IntCounterVec) -> Self {
        Self {
            registry,
            http_requests,
        }
    }
}

impl FromRef<AppState> for MetricsState {
    fn from_ref(app_state: &AppState) -> MetricsState {
        app_state.metrics_state.clone()
    }
}
