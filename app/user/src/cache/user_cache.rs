use crate::{
    error::{AppError, Result},
    models::User,
};
use bb8::Pool;
use bb8_redis::RedisConnectionManager;
use redis::AsyncCommands;
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct UserCache {
    pool: Pool<RedisConnectionManager>,
}

impl UserCache {
    pub fn new(pool: Pool<RedisConnectionManager>) -> Self {
        Self { pool }
    }

    /// Get user from cache
    pub async fn get_user(&self, user_id: Uuid) -> Result<Option<User>> {
        let mut conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        let key = format!("user:{}", user_id);

        let cached: Option<String> = conn
            .get(&key)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        match cached {
            Some(data) => {
                let user = serde_json::from_str(&data).map_err(|e| AppError::Internal(e.into()))?;
                Ok(Some(user))
            }
            _none => Ok(None),
        }
    }

    /// Store user in cache with 5 minute TTL
    pub async fn set_user(&self, user_id: Uuid, user: &User) -> Result<()> {
        let mut conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        let key = format!("user:{}", user_id);
        let data = serde_json::to_string(user).map_err(|e| AppError::Internal(e.into()))?;

        let _: () = conn
            .set_ex(&key, data, 300) // 5 minutes
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        Ok(())
    }

    /// Invalidate user cache
    pub async fn invalidate_user(&self, user_id: Uuid) -> Result<()> {
        let mut conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        let key = format!("user:{}", user_id);

        let _: () = conn
            .del(&key)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        Ok(())
    }

    /// Set user online status (ephemeral, 60 second TTL)
    pub async fn set_online(&self, user_id: Uuid, is_online: bool) -> Result<()> {
        let mut conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        let key = format!("presence:{}", user_id);

        if is_online {
            let _: () = conn
                .set_ex(&key, "1", 60) // 60 seconds - requires heartbeat
                .await
                .map_err(|e| AppError::Internal(e.into()))?;
        } else {
            let _: () = conn
                .del(&key)
                .await
                .map_err(|e| AppError::Internal(e.into()))?;
        }

        Ok(())
    }

    /// Check if user is online
    pub async fn is_online(&self, user_id: Uuid) -> Result<bool> {
        let mut conn = self
            .pool
            .get()
            .await
            .map_err(|e| AppError::Internal(e.into()))?;
        let key = format!("presence:{}", user_id);

        let exists: bool = conn
            .exists(&key)
            .await
            .map_err(|e| AppError::Internal(e.into()))?;

        Ok(exists)
    }
}
