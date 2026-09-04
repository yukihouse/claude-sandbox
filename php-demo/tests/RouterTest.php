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
}
