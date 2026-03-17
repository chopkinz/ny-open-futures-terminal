//! JARVIS Trading Engine - HTTP API entrypoint.

use std::net::SocketAddr;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

mod api;
mod config;
mod data;
mod session;
mod backtest;
mod setup;
mod alert;

use config::EngineConfig;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenvy::dotenv().ok();
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let config = EngineConfig::from_env();
    let app = api::router(config.clone());
    let addr = SocketAddr::from(([0, 0, 0, 0], config.port));
    tracing::info!("JARVIS Engine listening on http://{}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}
