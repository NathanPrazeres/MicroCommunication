use crate::{
    cache::{EventPublisher, UserCache},
    error::Result,
    models::{CreateUserRequest, UpdateUserRequest, User, UserEvent},
    repositories::UserRepository,
};
use uuid::Uuid;

/// UserService orchestrates all user-related operations
/// It coordinates between the database, cache, and event publishing
#[derive(Debug, Clone)]
pub struct UserService {
    repository: UserRepository,
    cache: UserCache,
    events: EventPublisher,
}

impl UserService {
    pub fn new(repository: UserRepository, cache: UserCache, events: EventPublisher) -> Self {
        Self {
            repository,
            cache,
            events,
        }
    }

    /// Create a new user
    pub async fn create_user(
        &self,
        user_id: Uuid,
        user_email: &str,
        user_name: &str,
        first_name: &str,
        last_name: &str,
        request: CreateUserRequest,
    ) -> Result<User> {
        let user = self
            .repository
            .create_user(
                user_id,
                user_name.to_string(),
                user_email.to_string(),
                first_name.to_string(),
                last_name.to_string(),
                request,
            )
            .await?;

        // 2. Store in cache for fast access
        self.cache.set_user(user.user_id, &user).await?;

        // 3. Publish event for other services
        self.events
            .publish(
                "events:users",
                &UserEvent::Created {
                    user_id: user.user_id,
                    username: user.username.clone(),
                    first_name: user.first_name.clone(),
                    last_name: user.last_name.clone(),
                },
            )
            .await?;

        tracing::info!("Created user: {}", user.user_id);

        Ok(user)
    }

    /// Get user by ID (with caching)
    pub async fn get_user(&self, id: Uuid) -> Result<User> {
        // 1. Try cache first (fast path)
        if let Some(user) = self.cache.get_user(id).await? {
            tracing::debug!("Cache HIT for user {}", id);
            return Ok(user);
        }

        tracing::debug!("Cache MISS for user {}", id);

        // 2. Cache miss - query database
        let user = self.repository.get_user(id).await?;

        // 3. Store in cache for next time (5 min TTL)
        self.cache.set_user(id, &user).await?;

        Ok(user)
    }

    /// Update user profile
    pub async fn update_user(&self, id: Uuid, request: UpdateUserRequest) -> Result<User> {
        // 1. Update in database
        let user = self.repository.update_user(id, request).await?;

        // 2. Invalidate cache (or update it)
        self.cache.invalidate_user(id).await?;

        // 3. Publish event
        self.events
            .publish(
                "events:users",
                &UserEvent::Updated {
                    user_id: user.user_id,
                    first_name: user.first_name.clone(),
                    last_name: user.last_name.clone(),
                    avatar_url: user.avatar_url.clone(),
                },
            )
            .await?;

        tracing::info!("Updated user: {}", id);

        Ok(user)
    }

    /// Delete user
    pub async fn delete_user(&self, id: Uuid) -> Result<()> {
        // 1. Delete from database
        let _: () = self.repository.delete_user(id).await?;

        // 2. Remove from cache
        self.cache.invalidate_user(id).await?;

        // 3. Publish event
        self.events
            .publish("events:users", &UserEvent::Deleted { user_id: id })
            .await?;

        tracing::info!("Deleted user: {}", id);

        Ok(())
    }

    /// Set user online status
    pub async fn set_online(&self, user_id: Uuid, is_online: bool) -> Result<()> {
        // Store in Redis only (ephemeral data)
        self.cache.set_online(user_id, is_online).await?;

        // Publish presence event
        self.events
            .publish(
                "events:users",
                &UserEvent::PresenceChanged { user_id, is_online },
            )
            .await?;

        Ok(())
    }

    /// Check if user is online
    pub async fn is_online(&self, user_id: Uuid) -> Result<bool> {
        self.cache.is_online(user_id).await
    }
}
