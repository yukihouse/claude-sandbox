const std = @import("std");

const PORT = 5006;

// 試し割り法による素数カウントの探索上限。Zig（ネイティブコンパイル）と
// Python（インタプリタ）に全く同じアルゴリズムを実装させ、実行時間を比較する。
const DEFAULT_N: u64 = 1_000_000;
const MIN_N: u64 = 10_000;
const MAX_N: u64 = 3_000_000;

pub fn main() !void {
    const allocator = std.heap.page_allocator;

    const address = try std.net.Address.parseIp("127.0.0.1", PORT);
    var server = try address.listen(.{ .reuse_address = true });
    defer server.deinit();

    std.debug.print("Listening on http://localhost:{d}\n", .{PORT});

    while (true) {
        const connection = server.accept() catch |err| {
            std.debug.print("accept error: {}\n", .{err});
            continue;
        };
        handleConnection(allocator, connection) catch |err| {
            std.debug.print("connection error: {}\n", .{err});
        };
    }
}

fn handleConnection(allocator: std.mem.Allocator, connection: std.net.Server.Connection) !void {
    defer connection.stream.close();

    var buf: [4096]u8 = undefined;
    const n = try connection.stream.read(&buf);
    const target = requestTarget(buf[0..n]) orelse "/";
    const path = pathOnly(target);

    if (std.mem.eql(u8, path, "/") or std.mem.eql(u8, path, "/index.html")) {
        try respondFile(allocator, connection.stream, "static/index.html", "text/html; charset=utf-8");
    } else if (std.mem.eql(u8, path, "/style.css")) {
        try respondFile(allocator, connection.stream, "static/style.css", "text/css; charset=utf-8");
    } else if (std.mem.eql(u8, path, "/api/benchmark")) {
        try handleBenchmark(allocator, connection.stream, target);
    } else {
        try writeResponse(connection.stream, "404 Not Found", "text/plain; charset=utf-8", "Not Found");
    }
}

// リクエストの1行目 "GET /path?query HTTP/1.1" からパス+クエリ部分だけを取り出す
fn requestTarget(request: []const u8) ?[]const u8 {
    const line_end = std.mem.indexOfScalar(u8, request, '\r') orelse request.len;
    const request_line = request[0..line_end];

    const method_end = std.mem.indexOfScalar(u8, request_line, ' ') orelse return null;
    const rest = request_line[method_end + 1 ..];

    const path_end = std.mem.indexOfScalar(u8, rest, ' ') orelse rest.len;
    return rest[0..path_end];
}

fn pathOnly(target: []const u8) []const u8 {
    const q = std.mem.indexOfScalar(u8, target, '?') orelse target.len;
    return target[0..q];
}

fn queryParam(target: []const u8, key: []const u8) ?[]const u8 {
    const q = std.mem.indexOfScalar(u8, target, '?') orelse return null;
    var it = std.mem.splitScalar(u8, target[q + 1 ..], '&');
    while (it.next()) |pair| {
        const eq = std.mem.indexOfScalar(u8, pair, '=') orelse continue;
        if (std.mem.eql(u8, pair[0..eq], key)) return pair[eq + 1 ..];
    }
    return null;
}

fn clampN(raw: ?[]const u8) u64 {
    const parsed = if (raw) |s| (std.fmt.parseInt(u64, s, 10) catch DEFAULT_N) else DEFAULT_N;
    if (parsed < MIN_N) return MIN_N;
    if (parsed > MAX_N) return MAX_N;
    return parsed;
}

fn isPrime(n: u64) bool {
    if (n < 2) return false;
    if (n % 2 == 0) return n == 2;
    var i: u64 = 3;
    while (i * i <= n) : (i += 2) {
        if (n % i == 0) return false;
    }
    return true;
}

// Python版（scripts/count_primes.py）と全く同じ試し割りアルゴリズム。
fn countPrimesNative(n: u64) u64 {
    var count: u64 = 0;
    var i: u64 = 2;
    while (i <= n) : (i += 1) {
        if (isPrime(i)) count += 1;
    }
    return count;
}

fn nsToMs(ns: u64) f64 {
    return @as(f64, @floatFromInt(ns)) / 1_000_000.0;
}

fn handleBenchmark(allocator: std.mem.Allocator, stream: std.net.Stream, target: []const u8) !void {
    const n = clampN(queryParam(target, "n"));

    var zig_timer = try std.time.Timer.start();
    const prime_count = countPrimesNative(n);
    const zig_ms = nsToMs(zig_timer.read());

    var n_buf: [32]u8 = undefined;
    const n_str = try std.fmt.bufPrint(&n_buf, "{d}", .{n});

    var python_ms: ?f64 = null;
    var python_error: ?[]const u8 = null;

    var py_timer = try std.time.Timer.start();
    if (std.process.Child.run(.{
        .allocator = allocator,
        .argv = &.{ "python3", "scripts/count_primes.py", n_str },
    })) |result| {
        defer allocator.free(result.stdout);
        defer allocator.free(result.stderr);
        const elapsed = nsToMs(py_timer.read());
        switch (result.term) {
            .Exited => |code| {
                if (code == 0) {
                    python_ms = elapsed;
                } else {
                    python_error = "python3 exited with a non-zero status";
                }
            },
            else => python_error = "python3 did not exit normally",
        }
    } else |err| {
        python_error = @errorName(err);
    }

    const body = try buildJson(allocator, n, prime_count, zig_ms, python_ms, python_error);
    defer allocator.free(body);

    try writeResponse(stream, "200 OK", "application/json; charset=utf-8", body);
}

fn buildJson(
    allocator: std.mem.Allocator,
    n: u64,
    prime_count: u64,
    zig_ms: f64,
    python_ms: ?f64,
    python_error: ?[]const u8,
) ![]u8 {
    var list: std.ArrayList(u8) = .empty;
    errdefer list.deinit(allocator);

    try list.appendSlice(allocator, "{");
    try list.print(allocator, "\"n\":{d},", .{n});
    try list.print(allocator, "\"primeCount\":{d},", .{prime_count});
    try list.print(allocator, "\"zigMs\":{d:.2},", .{zig_ms});
    if (python_ms) |ms| {
        try list.print(allocator, "\"pythonMs\":{d:.2},\"speedup\":{d:.1},", .{ ms, ms / zig_ms });
    } else {
        try list.appendSlice(allocator, "\"pythonMs\":null,\"speedup\":null,");
    }
    if (python_error) |e| {
        try list.print(allocator, "\"pythonError\":\"{s}\"", .{e});
    } else {
        try list.appendSlice(allocator, "\"pythonError\":null");
    }
    try list.appendSlice(allocator, "}");

    return list.toOwnedSlice(allocator);
}

fn respondFile(allocator: std.mem.Allocator, stream: std.net.Stream, path: []const u8, content_type: []const u8) !void {
    const file = std.fs.cwd().openFile(path, .{}) catch {
        try writeResponse(stream, "404 Not Found", "text/plain; charset=utf-8", "Not Found");
        return;
    };
    defer file.close();

    const body = try file.readToEndAlloc(allocator, 10 * 1024 * 1024);
    defer allocator.free(body);

    try writeResponse(stream, "200 OK", content_type, body);
}

fn writeResponse(stream: std.net.Stream, status: []const u8, content_type: []const u8, body: []const u8) !void {
    var header_buf: [256]u8 = undefined;
    const header = try std.fmt.bufPrint(
        &header_buf,
        "HTTP/1.1 {s}\r\nContent-Type: {s}\r\nContent-Length: {d}\r\nConnection: close\r\n\r\n",
        .{ status, content_type, body.len },
    );
    try stream.writeAll(header);
    try stream.writeAll(body);
}

const testing = std.testing;

test "requestTarget extracts the root path" {
    const target = requestTarget("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n");
    try testing.expectEqualStrings("/", target.?);
}

test "requestTarget keeps the query string" {
    const target = requestTarget("GET /api/benchmark?n=500000 HTTP/1.1\r\n");
    try testing.expectEqualStrings("/api/benchmark?n=500000", target.?);
}

test "pathOnly strips the query string" {
    try testing.expectEqualStrings("/api/benchmark", pathOnly("/api/benchmark?n=500000"));
    try testing.expectEqualStrings("/", pathOnly("/"));
}

test "queryParam finds the requested key" {
    const target = "/api/benchmark?n=500000&foo=bar";
    try testing.expectEqualStrings("500000", queryParam(target, "n").?);
    try testing.expectEqualStrings("bar", queryParam(target, "foo").?);
    try testing.expect(queryParam(target, "missing") == null);
    try testing.expect(queryParam("/api/benchmark", "n") == null);
}

test "clampN falls back to the default and clamps the range" {
    try testing.expectEqual(DEFAULT_N, clampN(null));
    try testing.expectEqual(DEFAULT_N, clampN("not-a-number"));
    try testing.expectEqual(MIN_N, clampN("1"));
    try testing.expectEqual(MAX_N, clampN("999999999"));
    try testing.expectEqual(@as(u64, 200_000), clampN("200000"));
}

test "isPrime matches known primes and composites" {
    try testing.expect(!isPrime(0));
    try testing.expect(!isPrime(1));
    try testing.expect(isPrime(2));
    try testing.expect(isPrime(3));
    try testing.expect(!isPrime(4));
    try testing.expect(isPrime(97));
    try testing.expect(!isPrime(100));
}

test "countPrimesNative counts primes below small bounds" {
    try testing.expectEqual(@as(u64, 0), countPrimesNative(1));
    try testing.expectEqual(@as(u64, 4), countPrimesNative(10));
    try testing.expectEqual(@as(u64, 25), countPrimesNative(100));
}

test "buildJson includes the computed fields" {
    const body = try buildJson(testing.allocator, 100, 25, 1.23, 45.6, null);
    defer testing.allocator.free(body);

    try testing.expect(std.mem.indexOf(u8, body, "\"n\":100") != null);
    try testing.expect(std.mem.indexOf(u8, body, "\"primeCount\":25") != null);
    try testing.expect(std.mem.indexOf(u8, body, "\"pythonMs\":45.60") != null);
    try testing.expect(std.mem.indexOf(u8, body, "\"pythonError\":null") != null);
}

test "buildJson reports a python error when present" {
    const body = try buildJson(testing.allocator, 100, 25, 1.23, null, "FileNotFound");
    defer testing.allocator.free(body);

    try testing.expect(std.mem.indexOf(u8, body, "\"pythonMs\":null") != null);
    try testing.expect(std.mem.indexOf(u8, body, "\"pythonError\":\"FileNotFound\"") != null);
}
