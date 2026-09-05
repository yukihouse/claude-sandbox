<?php

declare(strict_types=1);

namespace CounterDemo;

/**
 * カウンターの値をPHPセッションに保存する。
 * index.php でセッションクッキーの有効期限を長めに設定しているため、
 * ブラウザを閉じても（同じブラウザ・同じCookieであれば）値が消えない。
 */
final class CounterStore
{
    public function get(): int
    {
        return (int) ($_SESSION['count'] ?? 0);
    }

    public function increment(): int
    {
        $count = $this->get() + 1;
        $_SESSION['count'] = $count;

        return $count;
    }

    public function reset(): int
    {
        $_SESSION['count'] = 0;

        return 0;
    }
}
