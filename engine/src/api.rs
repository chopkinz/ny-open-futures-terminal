//! HTTP API: health, CORS, and future routes for data/setups/backtest/alerts.

use axum::{routing::get, Json, Router};
use tower_http::cors::{Any, CorsLayer};

use crate::config::EngineConfig;

#[derive(serde::Serialize)]
struct Health {
    status: &'static str,
    service: &'static str,
}

pub fn router(_config: EngineConfig) -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .route("/health", get(health))
        .layer(cors)
}

async fn health() -> Json<Health> {
    Json(Health {
        status: "ok",
        service: "jarvis-engine",
    })
}
