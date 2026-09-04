<?php

declare(strict_types=1);

namespace CounterDemo;

final class Router
{
    public function __construct(
        private readonly string $baseDir,
        private readonly CounterStore $counter = new CounterStore(),
    ) {
    }

    public function handle(string $path, string $method = 'GET'): Response
    {
        if ($method === 'GET' && ($path === '/' || $path === '/index.html')) {
            return $this->file($this->baseDir . '/templates/index.html', 'text/html; charset=utf-8');
        }

        if ($method === 'GET' && $path === '/style.css') {
            return $this->file($this->baseDir . '/static/style.css', 'text/css; charset=utf-8');
        }

        if ($method === 'GET' && $path === '/api/count') {
            return $this->json(['count' => $this->counter->get()]);
        }

        if ($method === 'POST' && $path === '/api/increment') {
            return $this->json(['count' => $this->counter->increment()]);
        }

        if ($method === 'POST' && $path === '/api/reset') {
            return $this->json(['count' => $this->counter->reset()]);
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

    /** @param array<string, int> $data */
    private function json(array $data): Response
    {
        return new Response(200, 'application/json', json_encode($data, JSON_THROW_ON_ERROR));
    }
}
