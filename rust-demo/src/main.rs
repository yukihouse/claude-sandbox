use axum::extract::State;
use axum::http::StatusCode;
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use serde::Serialize;
use std::sync::atomic::{AtomicU8, Ordering};
use std::sync::Arc;
use tower_http::services::{ServeDir, ServeFile};

// 「🛡️ 壊れないカウンター」機能。u8の上限（255）に達しても、Rustの
// checked_add でオーバーフローを検出し、安全に停止する（他言語にありがちな
// 「255の次が0に巻き戻る」ような挙動にはならない）ことを体感してもらう。
const NEAR_MAX: u8 = 250;

#[derive(Clone)]
struct AppState {
    safe_counter: Arc<AtomicU8>,
}

#[derive(Serialize)]
struct SafeCounterState {
    value: u8,
    max: u8,
}

#[derive(Serialize)]
struct SafeCounterError {
    error: &'static str,
    value: u8,
    max: u8,
}

fn app() -> Router {
    let state = AppState {
        safe_counter: Arc::new(AtomicU8::new(0)),
    };

    Router::new()
        .route_service("/", ServeFile::new("static/index.html"))
        .nest_service("/static", ServeDir::new("static"))
        .route("/api/safe-counter", get(get_safe_counter))
        .route("/api/safe-counter/increment", post(increment_safe_counter))
        .route("/api/safe-counter/jump-near-max", post(jump_near_max))
        .route("/api/safe-counter/reset", post(reset_safe_counter))
        .with_state(state)
}

async fn get_safe_counter(State(state): State<AppState>) -> Json<SafeCounterState> {
    Json(SafeCounterState {
        value: state.safe_counter.load(Ordering::SeqCst),
        max: u8::MAX,
    })
}

async fn increment_safe_counter(
    State(state): State<AppState>,
) -> Result<Json<SafeCounterState>, (StatusCode, Json<SafeCounterError>)> {
    state
        .safe_counter
        .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |value| {
            value.checked_add(1)
        })
        .map(|previous| {
            Json(SafeCounterState {
                value: previous + 1,
                max: u8::MAX,
            })
        })
        .map_err(|current| {
            (
                StatusCode::CONFLICT,
                Json(SafeCounterError {
                    error: "overflow blocked",
                    value: current,
                    max: u8::MAX,
                }),
            )
        })
}

async fn jump_near_max(State(state): State<AppState>) -> Json<SafeCounterState> {
    state.safe_counter.store(NEAR_MAX, Ordering::SeqCst);
    Json(SafeCounterState {
        value: NEAR_MAX,
        max: u8::MAX,
    })
}

async fn reset_safe_counter(State(state): State<AppState>) -> Json<SafeCounterState> {
    state.safe_counter.store(0, Ordering::SeqCst);
    Json(SafeCounterState {
        value: 0,
        max: u8::MAX,
    })
}

#[tokio::main]
async fn main() {
    let listener = tokio::net::TcpListener::bind("0.0.0.0:5001")
        .await
        .expect("failed to bind port 5001");

    println!("Listening on http://localhost:5001");
    axum::serve(listener, app()).await.expect("server error");
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::Body;
    use axum::http::{Request, StatusCode};
    use http_body_util::BodyExt;
    use tower::ServiceExt;

    #[tokio::test]
    async fn home_page_returns_ok_with_counter_markup() {
        let response = app()
            .oneshot(Request::builder().uri("/").body(Body::empty()).unwrap())
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = response.into_body().collect().await.unwrap().to_bytes();
        let body = String::from_utf8(body.to_vec()).unwrap();
        assert!(body.contains("カウンターデモ (Rust版)"));
    }

    #[tokio::test]
    async fn static_style_is_served() {
        let response = app()
            .oneshot(
                Request::builder()
                    .uri("/static/style.css")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn unknown_path_returns_not_found() {
        let response = app()
            .oneshot(
                Request::builder()
                    .uri("/unknown")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::NOT_FOUND);
    }

    #[tokio::test]
    async fn safe_counter_starts_at_zero() {
        let response = app()
            .oneshot(
                Request::builder()
                    .uri("/api/safe-counter")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = response.into_body().collect().await.unwrap().to_bytes();
        let body = String::from_utf8(body.to_vec()).unwrap();
        assert!(body.contains("\"value\":0"));
        assert!(body.contains("\"max\":255"));
    }

    #[tokio::test]
    async fn safe_counter_blocks_overflow_at_u8_max() {
        let app = app();

        let response = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/safe-counter/jump-near-max")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);

        // 250 -> 255 までの5回は正常にインクリメントできる
        for _ in 0..5 {
            let response = app
                .clone()
                .oneshot(
                    Request::builder()
                        .method("POST")
                        .uri("/api/safe-counter/increment")
                        .body(Body::empty())
                        .unwrap(),
                )
                .await
                .unwrap();
            assert_eq!(response.status(), StatusCode::OK);
        }

        // 255からさらに+1しようとするとオーバーフローするので安全にブロックされる
        let response = app
            .clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/safe-counter/increment")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::CONFLICT);

        let body = response.into_body().collect().await.unwrap().to_bytes();
        let body = String::from_utf8(body.to_vec()).unwrap();
        assert!(body.contains("\"value\":255"));
        assert!(body.contains("overflow blocked"));
    }

    #[tokio::test]
    async fn safe_counter_reset_returns_to_zero() {
        let app = app();

        app.clone()
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/safe-counter/jump-near-max")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let response = app
            .oneshot(
                Request::builder()
                    .method("POST")
                    .uri("/api/safe-counter/reset")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = response.into_body().collect().await.unwrap().to_bytes();
        let body = String::from_utf8(body.to_vec()).unwrap();
        assert!(body.contains("\"value\":0"));
    }
}
