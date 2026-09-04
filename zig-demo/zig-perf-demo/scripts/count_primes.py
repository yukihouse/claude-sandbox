import sys


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def count_primes(n: int) -> int:
    count = 0
    for i in range(2, n + 1):
        if is_prime(i):
            count += 1
    return count


if __name__ == "__main__":
    n = int(sys.argv[1])
    print(count_primes(n))
