use chrono::{DateTime, Utc};
use serde::Serialize;
use uuid::Uuid;

#[derive(Debug, Serialize)]
pub struct UserResponse {
    pub user_id: Uuid,
    pub username: String,
    pub first_name: String,
    pub last_name: String,
    pub avatar_url: Option<String>,
    pub bio: Option<String>,
    pub email: String,
    pub phone_number: Option<String>,
    pub is_online: bool,
    pub last_seen: DateTime<Utc>,

    pub nickname: Option<String>,
    pub is_favorite: bool,
    pub is_blocked: bool,
    pub contact_since: DateTime<Utc>,
}
