<?php

declare(strict_types=1);

namespace CounterDemo\Tests;

use CounterDemo\Router;
use PHPUnit\Framework\TestCase;

final class RouterTest extends TestCase
{
    private Router $router;

    protected function setUp(): void
    {
        $_SESSION = [];
        $this->router = new Router(dirname(__DIR__));
    }

    public function testHomePageReturnsCounterMarkup(): void
    {
        $response = $this->router->handle('/');

        self::assertSame(200, $response->status);
        self::assertStringContainsString('カウンターデモ (PHP版)', $response->body);
    }

    public function testStaticStyleIsServed(): void
    {
        $response = $this->router->handle('/style.css');

        self::assertSame(200, $response->status);
        self::assertSame('text/css; charset=utf-8', $response->contentType);
    }

    public function testUnknownPathReturnsNotFound(): void
    {
        $response = $this->router->handle('/unknown');

        self::assertSame(404, $response->status);
    }

    public function testCountApiStartsAtZero(): void
    {
        $response = $this->router->handle('/api/count');

        self::assertSame(200, $response->status);
        self::assertSame('application/json', $response->contentType);
        self::assertSame('{"count":0}', $response->body);
    }

    public function testIncrementPersistsAcrossRequests(): void
    {
        $this->router->handle('/api/increment', 'POST');
        $this->router->handle('/api/increment', 'POST');
        $response = $this->router->handle('/api/count');

        self::assertSame('{"count":2}', $response->body);
    }

    public function testResetSetsCountBackToZero(): void
    {
        $this->router->handle('/api/increment', 'POST');
        $response = $this->router->handle('/api/reset', 'POST');

        self::assertSame('{"count":0}', $response->body);
    }

    public function testIncrementRejectsGetMethod(): void
    {
        $response = $this->router->handle('/api/increment', 'GET');

        self::assertSame(404, $response->status);
    }
}
