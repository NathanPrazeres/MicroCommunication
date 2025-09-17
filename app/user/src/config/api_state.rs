use axum::extract::FromRef;

use crate::{ContactService, UserService, config::AppState};

#[derive(Debug, Clone)]
pub struct ApiState {
    pub user_service: UserService,
    pub contact_service: ContactService,
}

impl ApiState {
    pub fn new(user_service: UserService, contact_service: ContactService) -> Self {
        Self {
            user_service,
            contact_service,
        }
    }
}

impl FromRef<AppState> for ApiState {
    fn from_ref(app_state: &AppState) -> ApiState {
        app_state.api_state.clone()
    }
}
