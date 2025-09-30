use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::models::UserResponse;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserContact {
    pub user_id: Uuid,
    pub contact_id: Uuid,
    pub nickname: Option<String>,
    pub is_favorite: bool,
    pub is_blocked: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub deleted: bool,
}

#[derive(Debug, Deserialize)]
pub struct AddContactRequest {
    pub username: String,
}

#[derive(Debug, Deserialize)]
pub struct UpdateContactRequest {
    pub nickname: Option<String>,
    pub is_favorite: Option<bool>,
    pub is_blocked: Option<bool>,
}

impl From<UserContact> for UserResponse {
    fn from(contact: UserContact) -> Self {
        UserResponse {
            user_id: contact.contact_id,
            username: contact.nickname.clone().unwrap(),
            email: "".to_string(),
            first_name: "".to_string(),
            last_name: "".to_string(),
            bio: Some("".to_string()),
            avatar_url: Some("".to_string()),
            phone_number: Some("".to_string()),
            is_online: false,
            last_seen: DateTime::<Utc>::MIN_UTC,
            nickname: contact.nickname.clone(),
            is_favorite: contact.is_favorite,
            is_blocked: contact.is_blocked,
            contact_since: contact.created_at,
        }
    }
}
