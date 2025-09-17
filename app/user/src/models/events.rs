use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Events published to Redis Pub/Sub for other services to consume
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum UserEvent {
    Created {
        user_id: Uuid,
        username: String,
        first_name: String,
        last_name: String,
    },
    Updated {
        user_id: Uuid,
        first_name: String,
        last_name: String,
        avatar_url: Option<String>,
    },
    Deleted {
        user_id: Uuid,
    },
    PresenceChanged {
        user_id: Uuid,
        is_online: bool,
    },
}

impl UserEvent {
    /// Get the channel name for publishing
    pub fn channel(&self) -> &'static str {
        "events:users"
    }

    /// Wrap event with metadata
    pub fn into_envelope(self) -> EventEnvelope {
        EventEnvelope::new(self, Utc::now(), "user-service".to_string())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventEnvelope {
    pub event: UserEvent,
    pub timestamp: DateTime<Utc>,
    pub service: String,
}

impl EventEnvelope {
    pub fn new(event: UserEvent, timestamp: DateTime<Utc>, service: String) -> Self {
        Self {
            event,
            timestamp,
            service,
        }
    }
}
