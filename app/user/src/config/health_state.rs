use crate::{auth::jwks::JwksManager, config::AppState};
use axum::extract::FromRef;

#[derive(Clone)]
pub struct HealthState {
    pub db_pool: sqlx::PgPool,
    pub redis_pool: bb8::Pool<bb8_redis::RedisConnectionManager>,
    pub jwks: JwksManager,
}

impl HealthState {
    pub fn new(
        db_pool: sqlx::PgPool,
        redis_pool: bb8::Pool<bb8_redis::RedisConnectionManager>,
        jwks: JwksManager,
    ) -> Self {
        Self {
            db_pool,
            redis_pool,
            jwks,
        }
    }
}

impl FromRef<AppState> for HealthState {
    fn from_ref(app_state: &AppState) -> HealthState {
        app_state.health_state.clone()
    }
}
