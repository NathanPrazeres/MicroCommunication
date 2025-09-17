use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::models::UserResponse;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub user_id: Uuid,
    pub username: String,
    pub email: String,
    pub first_name: String,
    pub last_name: String,
    pub bio: Option<String>,
    pub avatar_url: Option<String>,
    pub phone_number: Option<String>,
    pub is_online: bool,
    pub last_seen: DateTime<Utc>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub deleted: bool,
}

#[derive(Debug, Deserialize)]
pub struct CreateUserRequest {
    pub bio: Option<String>,
    pub avatar_url: Option<String>,
    pub phone_number: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateUserRequest {
    pub bio: Option<String>,
    pub avatar_url: Option<String>,
}

impl From<User> for UserResponse {
    fn from(user: User) -> Self {
        UserResponse {
            user_id: user.user_id,
            username: user.username,
            email: user.email,
            first_name: user.first_name,
            last_name: user.last_name,
            bio: user.bio,
            avatar_url: user.avatar_url,
            phone_number: user.phone_number,
            is_online: user.is_online,
            last_seen: user.last_seen,
            nickname: None,
            is_favorite: false,
            is_blocked: false,
            contact_since: DateTime::<Utc>::MIN_UTC,
        }
    }
}
