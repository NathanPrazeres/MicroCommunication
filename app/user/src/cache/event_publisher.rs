use crate::error::AppError;
use bb8::Pool;
use bb8_redis::RedisConnectionManager;
use redis::AsyncCommands;
use serde::Serialize;

#[derive(Debug, Clone)]
pub struct EventPublisher {
    pool: Pool<RedisConnectionManager>,
}

impl EventPublisher {
    pub fn new(pool: Pool<RedisConnectionManager>) -> Self {
        Self { pool }
    }

    pub async fn publish<T>(&self, channel: &str, event: &T) -> Result<(), AppError>
    where
        T: Serialize,
    {
        // Serialize the event into JSON
        let payload = serde_json::to_string(event).map_err(|e| AppError::Internal(e.into()))?;

        // Get a Redis connection from the pool
        let conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        // Publish the event
        let _: () = conn
            .clone()
            .publish(channel, payload)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        Ok(())
    }
}
