use crate::{auth::jwt::JwtValidator, error::AppError};
use axum::{
    extract::{Request, State},
    http::header,
    middleware::Next,
    response::Response,
};

/// JWT Authentication Middleware
/// Extracts and validates JWT token from Authorization header
pub async fn jwt_middleware(
    State(validator): State<JwtValidator>,
    mut request: Request,
    next: Next,
) -> Result<Response, AppError> {
    let auth_header = request
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|h| h.to_str().ok())
        .ok_or(AppError::Unauthorized("Missing Authorization".into()))?;

    let token = JwtValidator::extract_token(auth_header)
        .ok_or(AppError::Unauthorized("Missing Bearer token".into()))?;

    let claims = validator.verify(token).await.map_err(anyhow::Error::from)?;

    tracing::debug!("Authenticated user: {:?} ({})", claims.username, claims.sub);

    // 4. Store claims in request extensions for handlers to use
    request.extensions_mut().insert(claims);

    // 5. Continue to the next handler
    Ok(next.run(request).await)
}
