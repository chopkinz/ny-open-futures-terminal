//! NY session and opening-range logic. All times canonical America/New_York.
//! Uses chrono-tz for DST-correct America/New_York.

use chrono::{DateTime, Datelike, NaiveDate, NaiveTime, TimeZone, Timelike, Utc};
use serde::Serialize;

/// Session config in NY time.
#[derive(Clone, Debug)]
pub struct SessionConfig {
    pub timezone: String,
    pub or_start: String,  // "09:30"
    pub or_end: String,    // "10:00"
    pub trade_window_end: String,
}

impl Default for SessionConfig {
    fn default() -> Self {
        Self {
            timezone: "America/New_York".to_string(),
            or_start: "09:30".to_string(),
            or_end: "10:00".to_string(),
            trade_window_end: "12:00".to_string(),
        }
    }
}

fn parse_hhmm(s: &str) -> Option<(u32, u32)> {
    let parts: Vec<&str> = s.trim().split(':').collect();
    if parts.len() < 2 {
        return None;
    }
    let h: u32 = parts[0].trim().parse().ok()?;
    let m: u32 = parts[1].trim().parse().ok()?;
    Some((h, m))
}

fn ny_tz() -> chrono_tz::America::NewYork {
    chrono_tz::America::NewYork
}

/// Session date for a UTC timestamp: before 04:00 NY = previous calendar day.
pub fn session_date_from_utc(utc: DateTime<Utc>) -> NaiveDate {
    let ny = utc.with_timezone(&ny_tz());
    let hour = ny.hour();
    let d = ny.date_naive();
    if hour < 4 {
        d.pred_opt().unwrap_or(d)
    } else {
        d
    }
}

/// Opening range bounds (start, end) in UTC for a given session date (NY).
pub fn or_bounds_utc(
    session_date: NaiveDate,
    or_start: &str,
    or_end: &str,
) -> Option<(DateTime<Utc>, DateTime<Utc>)> {
    let (sh, sm) = parse_hhmm(or_start)?;
    let (eh, em) = parse_hhmm(or_end)?;
    let t0 = NaiveTime::from_hms_opt(sh, sm, 0)?;
    let t1 = NaiveTime::from_hms_opt(eh, em, 0)?;
    let dt0 = session_date.and_time(t0);
    let dt1 = session_date.and_time(t1);
    let ny = chrono_tz::America::NewYork;
    let start_ny = ny.from_local_datetime(&dt0).single()?;
    let end_ny = ny.from_local_datetime(&dt1).single()?;
    Some((start_ny.with_timezone(&Utc), end_ny.with_timezone(&Utc)))
}

/// Trade window end in UTC for session date.
pub fn trade_window_end_utc(session_date: NaiveDate, end_time: &str) -> Option<DateTime<Utc>> {
    let (h, m) = parse_hhmm(end_time)?;
    let t = NaiveTime::from_hms_opt(h, m, 0)?;
    let dt = session_date.and_time(t);
    let ny = chrono_tz::America::NewYork;
    let end_ny = ny.from_local_datetime(&dt).single()?;
    Some(end_ny.with_timezone(&Utc))
}

pub fn is_weekday(d: NaiveDate) -> bool {
    d.weekday().num_days_from_monday() < 5
}

#[derive(Clone, Debug, Serialize)]
pub struct OpeningRange {
    pub date: String,
    pub or_high: f64,
    pub or_low: f64,
    pub or_mid: f64,
    pub or_width: f64,
    pub or_start_ts: String,
    pub or_end_ts: String,
    pub bar_count: usize,
    pub or_volume: f64,
}
