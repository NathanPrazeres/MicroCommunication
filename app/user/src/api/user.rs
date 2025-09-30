use tracing::{info, warn};
use uuid::Uuid;

use axum::{
    Extension, Router,
    extract::{Path, State},
    http::StatusCode,
    response::{IntoResponse, Json},
    routing::{delete, get, post, put},
};

use crate::{
    auth::Claims,
    config::{ApiState, AppState},
    models::{CreateUserRequest, UpdateUserRequest},
};

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/", post(create_user))
        // Get details of a specific user
        // needs to check if given ID is in
        // the user's contacts
        .route("/{id}", get(get_user))
        // Own user
        .route("/@me", put(update_user))
        .route("/@me", get(get_user_self))
        .route("/@me", delete(delete_user))
}

async fn create_user(
    Extension(claims): Extension<Claims>,
    State(state): State<ApiState>,
    Json(request): Json<CreateUserRequest>,
) -> impl IntoResponse {
    info!("Received `create_user` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!("Parsing email claim [{}] into string", claims.email.clone());
    let email = claims.email.clone();

    info!(
        "Parsing preferred_username claim [{}] into string",
        claims.preferred_username.clone()
    );
    let preferred_username = claims.preferred_username.clone();

    info!(
        "Parsing given_name claim [{}] into string",
        claims.given_name.clone()
    );
    let given_name = claims.given_name.clone();

    info!("Parsing family_name claim [{}] into string", claims.family_name.clone());
    let family_name = claims.family_name.clone();

    info!(
        "Calling `UserService::create_user` for [{}] with params {} {} {} {}",
        user_id, email, given_name, family_name, preferred_username
    );

    let user = state
        .user_service
        .create_user(user_id, &email, &preferred_username, &given_name, &family_name, request)
        .await
        .unwrap();

    (StatusCode::CREATED, Json(user))
}

async fn get_user(
    Extension(claims): Extension<Claims>,
    State(state): State<ApiState>,
    Path(id): Path<Uuid>,
) -> impl IntoResponse {
    info!("Received `get_user` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    let valid_user = state
        .contact_service
        .is_contact(&user_id, &id)
        .await
        .unwrap();

    if !valid_user {
        warn!("Queried user is not in the requesting user's contacts!")
    }

    info!("Calling `UserService::get_user` for [{}]", id);
    let user = state.user_service.get_user(id).await.unwrap();
    (StatusCode::OK, Json(user))
}

async fn get_user_self(
    State(state): State<ApiState>,
    Extension(claims): Extension<Claims>,
) -> impl IntoResponse {
    info!("Parsing sub claim [{}] into string", claims.sub.clone());
    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    let user = state.user_service.get_user(user_id).await.unwrap();
    (StatusCode::OK, Json(user))
}

async fn update_user(
    State(state): State<ApiState>,
    Extension(claims): Extension<Claims>,
    Json(request): Json<UpdateUserRequest>,
) -> impl IntoResponse {
    info!("Parsing sub claim [{}] into string", claims.sub.clone());
    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    let user = state.user_service.update_user(user_id, request).await.unwrap();
    (StatusCode::OK, Json(user))
}

async fn delete_user(
    State(state): State<ApiState>,
    Extension(claims): Extension<Claims>,
) -> impl IntoResponse {
    info!("Parsing sub claim [{}] into string", claims.sub.clone());
    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    let _ = state.user_service.delete_user(user_id).await;
    (StatusCode::NO_CONTENT, Json(()))
}
