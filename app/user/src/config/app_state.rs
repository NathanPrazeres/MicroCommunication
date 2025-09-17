use crate::config::{ApiState, HealthState, MetricsState};

#[derive(Clone)]
pub struct AppState {
    pub api_state: ApiState,
    pub health_state: HealthState,
    pub metrics_state: MetricsState,
}

impl AppState {
    pub fn new(
        api_state: ApiState,
        health_state: HealthState,
        metrics_state: MetricsState,
    ) -> Self {
        Self {
            api_state,
            health_state,
            metrics_state,
        }
    }
}
