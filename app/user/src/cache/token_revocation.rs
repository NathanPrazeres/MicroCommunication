use anyhow::Result;
use bb8::Pool;
use bb8_redis::RedisConnectionManager;
use chrono::Utc;
use redis::AsyncCommands;

use crate::error::AppError;

pub struct TokenRevocationCache {
    pool: Pool<RedisConnectionManager>,
}

impl TokenRevocationCache {
    pub fn new(pool: Pool<RedisConnectionManager>) -> Self {
        Self { pool }
    }

    /// Add token to blacklist
    pub async fn revoke_token(&self, jti: &str, exp: i64) -> Result<()> {
        let key = format!("revoked:{}", jti);
        let now = Utc::now().timestamp();
        let ttl = (exp - now).max(0) as u64; // TTL until token would expire anyway

        let conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        let _: () = conn
            .clone()
            .set_ex(&key, "1", ttl)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        Ok(())
    }

    /// Check if token is revoked
    pub async fn is_revoked(&self, jti: &str) -> Result<bool> {
        let mut conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        let key = format!("revoked:{}", jti);

        let exists: bool = conn
            .exists(&key)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        Ok(exists)
    }
}
