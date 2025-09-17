use axum::{
    Json,
    http::StatusCode,
    response::{IntoResponse, Response},
};
use serde::Serialize;

pub type Result<T> = std::result::Result<T, AppError>;

#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Bad request: {0}")]
    BadRequest(String),

    #[error("Conflict: {0}")]
    Conflict(String),

    #[error("Database error: {0}")]
    DatabaseError(#[from] sqlx::Error),

    #[error("Internal server error: {0}")]
    Internal(#[from] anyhow::Error),

    #[error("Validation error: {0}")]
    _ValidationError(String),
}

#[derive(Serialize)]
struct ErrorResponse {
    error: String,
    message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    details: Option<String>,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_type, message) = match &self {
            AppError::Unauthorized(msg) => (StatusCode::UNAUTHORIZED, "Unauthorized", msg.clone()),
            AppError::NotFound(msg) => (StatusCode::NOT_FOUND, "Not Found", msg.clone()),
            AppError::BadRequest(msg) => (StatusCode::BAD_REQUEST, "Bad Request", msg.clone()),
            AppError::Conflict(msg) => (StatusCode::CONFLICT, "Conflict", msg.clone()),
            AppError::DatabaseError(e) => {
                tracing::error!("Database error: {:?}", e);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "Database Error",
                    "An error occurred while accessing the database".to_string(),
                )
            }
            AppError::Internal(msg) => {
                tracing::error!("Internal error: {}", msg);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "Internal Server Error",
                    "An internal error occurred".to_string(),
                )
            }
            AppError::_ValidationError(msg) => (
                StatusCode::UNPROCESSABLE_ENTITY,
                "Validation Error",
                msg.clone(),
            ),
        };

        let body = Json(ErrorResponse {
            error: error_type.to_string(),
            message,
            details: None,
        });

        (status, body).into_response()
    }
}
