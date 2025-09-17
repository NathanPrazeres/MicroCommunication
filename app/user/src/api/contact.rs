use tracing::{info, instrument};
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
    models::{AddContactRequest, UpdateContactRequest},
};

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/", get(get_contacts))
        .route("/", post(add_contact))
        //
        .route("/{id}", delete(delete_contact))
        .route("/{id}", put(update_contact))
        //
        .route("/favorites", get(get_favorites))
        .route("/{id}/favorite", post(toggle_favorite))
        //
        .route("/blocked", get(get_blocked))
        .route("/{id}/block", post(block_user))
        .route("/{id}/unblock", post(unblock_user))
}

#[instrument]
async fn get_contacts(
    State(state): State<ApiState>,
    Extension(claims): Extension<Claims>,
) -> impl IntoResponse {
    info!("Received `get_contacts` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());
    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!(
        "Calling `ContactService::get_contacts` for [{}]'s contacts",
        user_id
    );
    let contacts = state.contact_service.get_contacts(user_id).await.unwrap();
    info!("Fetched {} contacts for [{}]", contacts.len(), user_id);

    (StatusCode::OK, Json(contacts))
}

#[instrument]
async fn add_contact(
    Extension(claims): Extension<Claims>,
    State(state): State<ApiState>,
    Json(request): Json<AddContactRequest>,
) -> impl IntoResponse {
    info!("Received `add_contact` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!(
        "Calling `ContactService::create_contact` for [{}] with params {:#?}",
        user_id, request
    );

    let user = state
        .contact_service
        .create_contact(user_id, request)
        .await
        .unwrap();

    info!("Contact created succesfully");

    (StatusCode::CREATED, Json(user))
}

#[instrument]
async fn delete_contact(
    Extension(claims): Extension<Claims>,
    State(state): State<ApiState>,
    Path(id): Path<Uuid>,
) -> impl IntoResponse {
    info!("Received `add_contact` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!(
        "Calling `ContactService::delete_contact` for [{}] with params {:#?}",
        user_id, id
    );

    let _ = state.contact_service.delete_contact(user_id, id);
    (StatusCode::NO_CONTENT, Json(()))
}

#[instrument]
async fn update_contact(
    State(state): State<ApiState>,
    Path(id): Path<Uuid>,
    Extension(claims): Extension<Claims>,
    Json(request): Json<UpdateContactRequest>,
) -> impl IntoResponse {
    info!("Received `add_contact` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!(
        "Calling `ContactService::update_contact` for [{}] with params {} {:#?}",
        user_id, id, request
    );

    let user = state
        .contact_service
        .update_contact(user_id, id, request)
        .await
        .unwrap();
    (StatusCode::OK, Json(user))
}

#[instrument]
async fn get_favorites(
    Extension(claims): Extension<Claims>,
    State(state): State<ApiState>,
) -> impl IntoResponse {
    info!("Received `add_contact` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!("Calling `ContactService::get_favorites` for [{}]", user_id);

    let favorites = state.contact_service.get_favorites(&user_id).await.unwrap();
    (StatusCode::OK, Json(favorites))
}

#[instrument]
async fn toggle_favorite(
    Extension(claims): Extension<Claims>,
    State(state): State<ApiState>,
    Path(id): Path<Uuid>,
) -> impl IntoResponse {
    info!("Received `add_contact` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!(
        "Calling `ContactService::toggle_favorite` for [{}] with params {}",
        user_id, id
    );

    let contact = state
        .contact_service
        .toggle_favorite(&user_id, &id)
        .await
        .unwrap();
    (StatusCode::OK, Json(contact))
}

#[instrument]
async fn get_blocked(
    State(state): State<ApiState>,
    Extension(claims): Extension<Claims>,
) -> impl IntoResponse {
    info!("Received `add_contact` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!("Calling `ContactService::get_blocked` for [{}]", user_id);

    let blocked = state.contact_service.get_blocked(&user_id).await.unwrap();

    (StatusCode::OK, Json(blocked))
}

#[instrument]
async fn block_user(
    Extension(claims): Extension<Claims>,
    State(state): State<ApiState>,
    Path(id): Path<Uuid>,
) -> impl IntoResponse {
    info!("Received `add_contact` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!(
        "Calling `ContactService::block_contact` for [{}] with params {}",
        user_id, id
    );

    state
        .contact_service
        .block_contact(&user_id, &id)
        .await
        .unwrap();

    (StatusCode::NO_CONTENT, Json(()))
}

#[instrument]
async fn unblock_user(
    Extension(claims): Extension<Claims>,
    State(state): State<ApiState>,
    Path(id): Path<Uuid>,
) -> impl IntoResponse {
    info!("Received `add_contact` call");
    info!("Parsing sub claim [{}] into string", claims.sub.clone());

    let user_id = Uuid::parse_str(claims.sub.as_ref()).expect("valid user_id");

    info!(
        "Calling `ContactService::unblock_contact` for [{}] with params {}",
        user_id, id
    );

    state
        .contact_service
        .unblock_contact(&user_id, &id)
        .await
        .unwrap();

    (StatusCode::NO_CONTENT, Json(()))
}
