//! Engine configuration from environment.

use std::env;

#[derive(Clone, Debug)]
pub struct EngineConfig {
    pub port: u16,
    pub cache_dir: String,
    pub polygon_api_key: Option<String>,
    pub alpha_vantage_api_key: Option<String>,
    pub timezone: String,
    pub or_start: String,
    pub or_end: String,
    pub trade_window_end: String,
}

impl Default for EngineConfig {
    fn default() -> Self {
        Self {
            port: 3001,
            cache_dir: "data/cache".to_string(),
            polygon_api_key: None,
            alpha_vantage_api_key: None,
            timezone: "America/New_York".to_string(),
            or_start: "09:30".to_string(),
            or_end: "10:00".to_string(),
            trade_window_end: "12:00".to_string(),
        }
    }
}

impl EngineConfig {
    pub fn from_env() -> Self {
        let port = env::var("PORT")
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(3001);
        let cache_dir = env::var("CACHE_DIR").unwrap_or_else(|_| "data/cache".to_string());
        let polygon_api_key = env::var("POLYGON_API_KEY").ok();
        let alpha_vantage_api_key = env::var("ALPHA_VANTAGE_API_KEY").ok();
        let timezone = env::var("SESSION_TIMEZONE").unwrap_or_else(|_| "America/New_York".to_string());
        let or_start = env::var("OR_START").unwrap_or_else(|_| "09:30".to_string());
        let or_end = env::var("OR_END").unwrap_or_else(|_| "10:00".to_string());
        let trade_window_end = env::var("TRADE_WINDOW_END").unwrap_or_else(|_| "12:00".to_string());

        Self {
            port,
            cache_dir,
            polygon_api_key,
            alpha_vantage_api_key,
            timezone,
            or_start,
            or_end,
            trade_window_end,
        }
    }
}
