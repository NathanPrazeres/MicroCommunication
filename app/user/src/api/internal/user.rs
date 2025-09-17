use uuid::Uuid;

use axum::{
    Router,
    extract::{Path, State},
    http::StatusCode,
    response::{IntoResponse, Json},
    routing::get,
};

use crate::config::{ApiState, AppState};

pub fn routes() -> Router<AppState> {
    Router::new()
        // Get details of a specific user
        // needs to check if given ID is in
        // the user's contacts
        .route("/{id}", get(get_user))
}

async fn get_user(State(state): State<ApiState>, Path(id): Path<Uuid>) -> impl IntoResponse {
    let user = state.user_service.get_user(id).await.unwrap();
    (StatusCode::OK, Json(user))
}
