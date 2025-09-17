use crate::{
    cache::UserCache,
    error::AppError,
    models::{CreateUserRequest, UpdateUserRequest, User},
};
use anyhow::{Ok, Result};
use sqlx::PgPool;
use tracing::info;
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct UserRepository {
    db_pool: PgPool,
    cache: UserCache,
}

impl UserRepository {
    pub fn new(db_pool: PgPool, cache: UserCache) -> Self {
        Self { db_pool, cache }
    }

    pub async fn create_user(
        &self,
        user_id: Uuid,
        username: String,
        email: String,
        first_name: String,
        last_name: String,
        request: CreateUserRequest,
    ) -> Result<User> {
        // Insert into database with proper column mapping
        let user = sqlx::query_as!(
            User,
            r#"
            INSERT INTO user_profiles (
                user_id,
                username,
                email,
                first_name,
                last_name,
                bio,
                avatar_url,
                phone_number,
                last_seen,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW(), NOW())
            RETURNING *
            "#,
            user_id,
            username,
            email,
            first_name,
            last_name,
            request.bio,
            request.avatar_url,
            request.phone_number,
        )
        .fetch_one(&self.db_pool)
        .await
        .map_err(|e| {
            tracing::error!(
                "Failed to insert user '{}' (keycloak_id: {}): {}",
                username,
                user_id,
                e
            );

            // Better error messages based on error type
            match e {
                sqlx::Error::Database(db_err) => {
                    if db_err.is_unique_violation() {
                        AppError::Conflict(format!("User '{}' already exists", username))
                    } else if db_err.is_foreign_key_violation() {
                        AppError::BadRequest("Invalid Keycloak user ID".to_string())
                    } else {
                        AppError::DatabaseError(sqlx::Error::Database(db_err))
                    }
                }
                _ => AppError::DatabaseError(e),
            }
        })?;

        Ok(user)
    }

    pub async fn delete_user(&self, id: Uuid) -> Result<()> {
        info!("Received delete_user call with id: {}", id);
        sqlx::query_as!(
            User,
            "UPDATE user_profiles SET deleted = TRUE
             WHERE user_id = $1 RETURNING *",
            id
        )
        .fetch_one(&self.db_pool)
        .await?;
        Ok(())
    }

    pub async fn get_user(&self, id: Uuid) -> Result<User> {
        if let Some(user) = self.cache.get_user(id).await? {
            tracing::debug!("Cache hit for user {}", id);
            return Ok(user);
        }

        tracing::debug!("Cache miss for user {}", id);

        let user = sqlx::query_as!(User, "SELECT * FROM user_profiles WHERE user_id = $1", id)
            .fetch_one(&self.db_pool)
            .await
            .map_err(|_| AppError::NotFound("User with the given ID not found".to_string()))?;

        self.cache.set_user(id, &user).await?;

        Ok(user)
    }

    pub async fn update_user(&self, id: Uuid, request: UpdateUserRequest) -> Result<User> {
        let user = sqlx::query_as!(
            User,
            "UPDATE user_profiles SET bio = $2, avatar_url = $3, updated_at = NOW() 
             WHERE user_id = $1 RETURNING *",
            id,
            request.bio,
            request.avatar_url
        )
        .fetch_one(&self.db_pool)
        .await
        .map_err(|_| AppError::NotFound("User with the given ID not found".to_string()))?;

        self.cache.set_user(id, &user).await?;

        Ok(user)
    }
}
