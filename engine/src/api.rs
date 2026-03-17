//! HTTP API: health, session (NY Open), CORS. Times in UTC; frontend renders in user local.

use axum::{extract::State, routing::get, Json, Router};
use chrono::Utc;
use std::sync::Arc;
use tower_http::cors::{Any, CorsLayer};

use crate::config::EngineConfig;
use crate::session;

#[derive(Clone)]
pub struct AppState(Arc<EngineConfig>);

#[derive(serde::Serialize)]
struct Health {
    status: &'static str,
    service: &'static str,
}

/// Today's NY session: OR bounds and trade window end in UTC (ISO). Frontend converts to local.
#[derive(serde::Serialize)]
struct SessionToday {
    session_date: String,
    or_start_utc: String,
    or_end_utc: String,
    trade_window_end_utc: String,
    timezone: String,
}

pub fn router(config: EngineConfig) -> Router {
    let state = AppState(Arc::new(config));
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .route("/health", get(health))
        .route("/api/session/today", get(session_today))
        .layer(cors)
        .with_state(state)
}

async fn health() -> Json<Health> {
    Json(Health {
        status: "ok",
        service: "jarvis-engine",
    })
}

async fn session_today(State(state): State<AppState>) -> Json<SessionToday> {
    let cfg = &state.0;
    let now = Utc::now();
    let session_date = session::session_date_from_utc(now);
    let session_date_str = session_date.format("%Y-%m-%d").to_string();
    let (or_start, or_end) = session::or_bounds_utc(
        session_date,
        &cfg.or_start,
        &cfg.or_end,
    ).unwrap_or((now, now));
    let tw_end = session::trade_window_end_utc(session_date, &cfg.trade_window_end)
        .unwrap_or(now);
    Json(SessionToday {
        session_date: session_date_str,
        or_start_utc: or_start.to_rfc3339(),
        or_end_utc: or_end.to_rfc3339(),
        trade_window_end_utc: tw_end.to_rfc3339(),
        timezone: cfg.timezone.clone(),
    })
}
