use axum::Router;
use tower_http::services::{ServeDir, ServeFile};

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route_service("/", ServeFile::new("static/index.html"))
        .nest_service("/static", ServeDir::new("static"));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:5001")
        .await
        .expect("failed to bind port 5001");

    println!("Listening on http://localhost:5001");
    axum::serve(listener, app).await.expect("server error");
}
