use std::env;
use std::num::ParseIntError;

use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    // Database
    pub database_url: String,

    // Redis
    pub redis_url: String,
    pub redis_ttl_seconds: u64,
    pub redis_cache_enabled: bool,

    // Keycloak
    pub keycloak_url: String,
    pub keycloak_realm: String,

    // Server
    pub service_port: u16,

    // Logging
    pub rust_log: String,
    pub rust_backtrace: String,

    // Environment
    pub environment: Environment,
}

#[derive(Debug, Clone, Deserialize, PartialEq)]
pub enum Environment {
    Development,
    Production,
}

impl Config {
    pub fn from_env() -> Result<Self, ConfigError> {
        Ok(Self {
            database_url: env::var("DATABASE_URL")?,
            redis_url: env::var("REDIS_URL")?,
            redis_ttl_seconds: env::var("REDIS_TTL_SECONDS")?.parse::<u64>().unwrap(),
            redis_cache_enabled: env::var("REDIS_CACHE_ENABLED")?.parse::<bool>().unwrap(),
            keycloak_url: env::var("KEYCLOAK_URL")?,
            keycloak_realm: env::var("KEYCLOAK_REALM")?,
            service_port: env::var("SERVICE_PORT")?.parse()?,
            rust_log: env::var("RUST_LOG")?,
            rust_backtrace: env::var("RUST_BACKTRACE")?,
            environment: match env::var("ENVIRONMENT").as_deref() {
                Ok("production") => Environment::Production,
                _ => Environment::Development,
            },
        })
    }
}

#[derive(Debug)]
pub enum ConfigError {
    MissingVar(std::env::VarError),
    ParseError(ParseIntError),
}

impl From<std::env::VarError> for ConfigError {
    fn from(err: std::env::VarError) -> Self {
        ConfigError::MissingVar(err)
    }
}

impl From<ParseIntError> for ConfigError {
    fn from(err: ParseIntError) -> Self {
        ConfigError::ParseError(err)
    }
}
