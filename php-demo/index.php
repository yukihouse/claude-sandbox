<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use CounterDemo\Router;

// カウンターがブラウザを閉じても消えないよう、セッションクッキーの有効期限を30日にしておく
session_set_cookie_params(['lifetime' => 60 * 60 * 24 * 30, 'path' => '/']);
session_start();

$router = new Router(__DIR__);
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?? '/';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$response = $router->handle($path, $method);

http_response_code($response->status);
header('Content-Type: ' . $response->contentType);
echo $response->body;
