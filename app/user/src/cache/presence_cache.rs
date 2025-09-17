use anyhow::{Ok, Result};
use bb8::Pool;
use bb8_redis::RedisConnectionManager;
use redis::AsyncCommands;
use uuid::Uuid;

use crate::error::AppError;

pub struct PresenceCache {
    pool: Pool<RedisConnectionManager>,
}

impl PresenceCache {
    pub fn new(pool: Pool<RedisConnectionManager>) -> Self {
        Self { pool }
    }

    /// Mark user as online
    pub async fn set_online(&self, user_id: Uuid) -> Result<()> {
        let key = format!("presence:{}", user_id);

        let conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        // Set with 60 second TTL - user must heartbeat to stay online
        let _: () = conn
            .clone()
            .set_ex(&key, "online", 60)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        // Add to online users set
        let _: () = conn
            .clone()
            .sadd("online_users", user_id.to_string())
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        Ok(())
    }

    /// Heartbeat - extend online status
    pub async fn heartbeat(&self, user_id: Uuid) -> Result<()> {
        let key = format!("presence:{}", user_id);

        let conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        let _: () = conn
            .clone()
            .expire(&key, 60)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        Ok(())
    }

    /// Get all online users
    pub async fn get_online_users(&self) -> Result<Vec<Uuid>> {
        let conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        let users: Vec<String> = conn.clone().smembers("online_users").await?;

        Ok(users
            .into_iter()
            .filter_map(|s| Uuid::parse_str(&s).ok())
            .collect())
    }

    /// Check if specific user is online
    pub async fn is_online(&self, user_id: Uuid) -> Result<bool> {
        let conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        let key = format!("presence:{}", user_id);

        let exists: bool = conn.clone().exists(&key).await?;
        Ok(exists)
    }
}
