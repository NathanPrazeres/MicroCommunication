use crate::{
    error::AppError,
    models::{AddContactRequest, UpdateContactRequest, UserContact, UserResponse},
};

use anyhow::{Ok, Result};
use sqlx::PgPool;
use tracing::info;
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct ContactRepository {
    db_pool: PgPool,
}

impl ContactRepository {
    pub fn new(db_pool: PgPool) -> Self {
        Self { db_pool }
    }

    pub async fn create_contact(
        &self,
        user_id: Uuid,
        request: AddContactRequest,
    ) -> Result<UserContact> {
        tracing::info!(
            "Creating contact for user {} with contact {:?}",
            user_id,
            request
        );

        let contact = sqlx::query_as!(
            UserContact,
            r#"
        INSERT INTO user_contacts (
            user_id, contact_id, nickname,
            is_favorite, is_blocked, created_at, updated_at
        )
        VALUES ($1, $2, $3, false, false, NOW(), NOW())
        RETURNING *
        "#,
            user_id,
            request.contact_id,
            request.nickname
        )
        .fetch_one(&self.db_pool)
        .await
        .map_err(|e| {
            tracing::error!(
                "Failed to insert contact '{}' (keycloak_id: {}): {}",
                request.contact_id,
                user_id,
                e
            );

            // Better error messages based on error type
            match e {
                sqlx::Error::Database(db_err) => {
                    if db_err.is_unique_violation() {
                        AppError::Conflict(format!(
                            "Contact '{}' already exists",
                            request.contact_id
                        ))
                    } else if db_err.is_foreign_key_violation() {
                        AppError::BadRequest("Invalid Keycloak user ID".to_string())
                    } else {
                        AppError::DatabaseError(sqlx::Error::Database(db_err))
                    }
                }
                _ => AppError::DatabaseError(e),
            }
        })?;

        Ok(contact)
    }

    pub async fn remove_contact(&self, user_id: Uuid, contact_id: Uuid) -> Result<()> {
        info!(
            "Received delete_contact call with user_id: {} and contact_id: {}",
            user_id, contact_id
        );
        sqlx::query!(
            r#"UPDATE user_contacts SET deleted = TRUE
            WHERE user_id = $1 and contact_id = $2 RETURNING *"#,
            user_id,
            contact_id,
        )
        .fetch_one(&self.db_pool)
        .await?;

        Ok(())
    }

    pub async fn get_contacts(&self, user_id: Uuid) -> Result<Vec<UserContact>> {
        let contacts = sqlx::query_as!(
            UserContact,
            r#"
            SELECT * FROM user_contacts
            WHERE user_id = $1 AND is_blocked = false
            ORDER BY is_favorite DESC, created_at DESC
            "#,
            user_id
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(contacts)
    }

    pub async fn get_contacts_with_profiles(&self, user_id: &Uuid) -> Result<Vec<UserResponse>> {
        let contacts = sqlx::query_as!(
            UserResponse,
            r#"
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                u.last_name,
                u.avatar_url,
                u.bio,
                u.email,
                u.phone_number,
                u.is_online,
                u.last_seen,
                uc.nickname,
                uc.is_favorite,
                uc.is_blocked,
                uc.created_at as contact_since
            FROM user_contacts uc
            INNER JOIN user_profiles u ON u.user_id = uc.contact_id
            WHERE uc.user_id = $1
            AND uc.is_blocked = false
            ORDER BY uc.is_favorite DESC, uc.created_at DESC
            "#,
            user_id
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(contacts)
    }

    pub async fn update_contact(
        &self,
        user_id: Uuid,
        contact_user_id: Uuid,
        request: UpdateContactRequest,
    ) -> Result<UserContact> {
        let contact = sqlx::query_as!(
            UserContact,
            r#"
        UPDATE user_contacts
        SET
            nickname = COALESCE($3, nickname),
            is_favorite = COALESCE($4, is_favorite),
            is_blocked = COALESCE($5, is_blocked),
            updated_at = NOW()
        WHERE user_id = $1 AND contact_id = $2
        RETURNING *
        "#,
            user_id,
            contact_user_id,
            request.nickname,
            request.is_favorite,
            request.is_blocked
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or_else(|| AppError::NotFound("Contact not found".into()))?;

        Ok(contact)
    }

    pub async fn get_favorites(&self, user_id: &Uuid) -> Result<Vec<UserContact>> {
        let contacts = sqlx::query_as!(
            UserContact,
            "SELECT * FROM user_contacts WHERE user_id = $1 AND is_favorite = true",
            user_id
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(contacts)
    }

    pub async fn toggle_favorite(
        &self,
        user_id: &Uuid,
        contact_user_id: &Uuid,
    ) -> Result<UserResponse> {
        // Toggle the favorite status
        let contact = sqlx::query_as!(
            UserResponse,
            r#"
            WITH updated AS (
                UPDATE user_contacts
                SET is_favorite = NOT is_favorite,
                    updated_at = NOW()
                WHERE user_id = $1 AND contact_id = $2
                RETURNING *
            )
            SELECT
                u.user_id,
                u.username,
                u.email,
                u.first_name,
                u.last_name,
                u.avatar_url,
                u.phone_number,
                u.bio,
                false as "is_online!",
                u.updated_at as last_seen,
                updated.nickname,
                updated.is_favorite as "is_favorite!",
                updated.is_blocked as "is_blocked!",
                updated.created_at as contact_since
            FROM updated
            INNER JOIN user_profiles u ON u.user_id = updated.contact_id
            "#,
            user_id,
            contact_user_id
        )
        .fetch_optional(&self.db_pool)
        .await?
        .ok_or_else(|| AppError::NotFound("Contact not found".to_string()))?;

        Ok(contact)
    }

    /// Get blocked contacts
    pub async fn get_blocked(&self, user_id: &Uuid) -> Result<Vec<UserContact>> {
        let contacts = sqlx::query_as!(
            UserContact,
            "SELECT * FROM user_contacts WHERE user_id = $1 AND is_blocked = true",
            user_id
        )
        .fetch_all(&self.db_pool)
        .await?;

        Ok(contacts)
    }

    pub async fn set_blocked(
        &self,
        user_id: &Uuid,
        contact_user_id: &Uuid,
        blocked: bool,
    ) -> Result<()> {
        let result = sqlx::query!(
            r#"
            UPDATE user_contacts
            SET is_blocked = $3,
                updated_at = NOW()
            WHERE user_id = $1 AND contact_id = $2
            "#,
            user_id,
            contact_user_id,
            blocked
        )
        .execute(&self.db_pool)
        .await?;

        if result.rows_affected() == 0 {
            return Err(AppError::NotFound("Contact not found".to_string()).into());
        }

        Ok(())
    }

    pub async fn contact_exists_for_user(
        &self,
        user_id: &Uuid,
        contact_user_id: &Uuid,
    ) -> Result<bool> {
        let exists = sqlx::query!(
            r#"
        SELECT contact_id FROM user_contacts WHERE user_id = $1 AND contact_id = $2
        "#,
            user_id,
            contact_user_id
        )
        .fetch_optional(&self.db_pool)
        .await?;

        Ok(exists.is_some())
    }
}
