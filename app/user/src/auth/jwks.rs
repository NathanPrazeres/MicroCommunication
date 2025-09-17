use anyhow::{Ok, Result, bail};
use jsonwebtoken::DecodingKey;
use reqwest::Client;
use serde::Deserialize;
use std::{
    collections::HashMap,
    sync::Arc,
    time::{Duration, Instant},
};
use tokio::sync::RwLock;
use tracing::{info, warn};

#[derive(Debug, Deserialize, Clone)]
pub struct JwksResponse {
    pub keys: Vec<Jwk>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Jwk {
    pub kid: String,
    pub kty: String,
    pub alg: String,
    pub n: String,
    pub e: String,
}

#[derive(Clone)]
struct JwksCache {
    keys: HashMap<String, DecodingKey>,
    last_refresh: Instant,
}

#[derive(Clone)]
pub struct JwksManager {
    cache: Arc<RwLock<JwksCache>>,
    jwks_url: String,
    client: Client,
}

impl JwksManager {
    pub fn new(jwks_url: String) -> Self {
        Self {
            cache: Arc::new(RwLock::new(JwksCache {
                keys: HashMap::new(),
                last_refresh: Instant::now() - Duration::from_secs(3600),
            })),
            jwks_url,
            client: Client::new(),
        }
    }

    /// Get the decoding key for a given `kid` (fetch + cache)
    pub async fn get_key(&self, kid: &str) -> anyhow::Result<DecodingKey> {
        {
            // Fast path: read-only access
            let cache = self.cache.read().await;
            if let Some(key) = cache.keys.get(kid) {
                info!("Cache hit for kid [{}]", kid);
                return Ok(key.clone());
            }
        }

        // If not found, refresh (will short-circuit if recent)
        self.refresh().await?;

        let cache = self.cache.read().await;
        cache
            .keys
            .get(kid)
            .cloned()
            .ok_or_else(|| anyhow::anyhow!("KID '{}' not found in JWKS", kid))
    }

    /// Refresh the JWKS cache (only if needed)
    pub async fn refresh(&self) -> anyhow::Result<()> {
        {
            let cache = self.cache.read().await;
            if cache.last_refresh.elapsed() < Duration::from_secs(300) {
                info!("JWKS refresh skipped (too recent)");
                return Ok(());
            }
        }

        info!("Refreshing JWKS from {}", &self.jwks_url);

        let resp = self
            .client
            .get(&self.jwks_url)
            .send()
            .await?
            .error_for_status()?;

        let jwks = resp.json::<JwksResponse>().await?;

        info!("JWKS casted response: {:#?}", jwks);

        let mut new_keys = HashMap::new();
        for jwk in jwks.keys {
            match jwk_to_decoding_key(&jwk) {
                std::result::Result::Ok(key) => {
                    new_keys.insert(jwk.kid.clone(), key);
                }
                Err(err) => {
                    warn!("Skipping unsupported JWK [{}]: {}", jwk.kid, err);
                }
            }
        }

        let mut cache = self.cache.write().await;
        cache.keys = new_keys;
        cache.last_refresh = Instant::now();

        info!("JWKS refresh complete");
        Ok(())
    }
}

fn jwk_to_decoding_key(jwk: &Jwk) -> Result<DecodingKey> {
    if jwk.kty != "RSA" {
        bail!("Unsupported key type: {}", jwk.kty);
    }
    if jwk.alg != "RS256" {
        bail!("Unsupported algorithm: {}", jwk.alg);
    }

    Ok(DecodingKey::from_rsa_components(&jwk.n, &jwk.e)?)
}
