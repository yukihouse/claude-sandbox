<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use CounterDemo\Router;

$router = new Router(__DIR__);
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?? '/';
$response = $router->handle($path);

http_response_code($response->status);
header('Content-Type: ' . $response->contentType);
echo $response->body;
