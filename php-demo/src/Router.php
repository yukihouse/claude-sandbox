<?php

declare(strict_types=1);

namespace CounterDemo;

final class Router
{
    public function __construct(private readonly string $baseDir)
    {
    }

    public function handle(string $path): Response
    {
        if ($path === '/' || $path === '/index.html') {
            return $this->file($this->baseDir . '/templates/index.html', 'text/html; charset=utf-8');
        }

        if ($path === '/style.css') {
            return $this->file($this->baseDir . '/static/style.css', 'text/css; charset=utf-8');
        }

        return new Response(404, 'text/plain; charset=utf-8', 'Not Found');
    }

    private function file(string $filePath, string $contentType): Response
    {
        if (!is_file($filePath)) {
            return new Response(404, 'text/plain; charset=utf-8', 'Not Found');
        }

        return new Response(200, $contentType, file_get_contents($filePath));
    }
}
