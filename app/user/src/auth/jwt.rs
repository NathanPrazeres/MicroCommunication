use jsonwebtoken::{Algorithm, Validation, decode};
use serde::{Deserialize, Serialize};

use crate::auth::jwks::JwksManager;

#[derive(Clone)]
pub struct JwtValidator {
    pub jwks: JwksManager,
    pub validation: Validation,
}

impl JwtValidator {
    pub fn new(jwks: JwksManager) -> Self {
        let mut validation = Validation::new(Algorithm::RS256);
        validation.validate_aud = false;

        Self {
            jwks,
            validation,
        }
    }

    pub async fn verify(&self, token: &str) -> Result<Claims, jsonwebtoken::errors::Error> {
        let header = jsonwebtoken::decode_header(token)?;
        let kid = header.kid.expect("Header should have KID.");

        let key = self.jwks.get_key(&kid).await.map_err(|_| {
            jsonwebtoken::errors::Error::from(jsonwebtoken::errors::ErrorKind::InvalidSignature)
        })?;

        let token_data = decode::<Claims>(token, &key, &self.validation)?;
        Ok(token_data.claims)
    }

    pub fn extract_token(auth_header: &str) -> Option<&str> {
        auth_header.strip_prefix("Bearer ")
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Claims {
    pub sub: String,
    pub preferred_username: String,
    pub email: String,
    pub given_name: String,
    pub family_name: String,
    pub exp: usize,
    pub iat: usize,
    pub jti: String,
}
