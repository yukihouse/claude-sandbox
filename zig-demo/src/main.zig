const std = @import("std");

const PORT = 5005;

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
    const target = requestPath(buf[0..n]) orelse "/";

    const query_start = std.mem.indexOfScalar(u8, target, '?');
    const path = if (query_start) |idx| target[0..idx] else target;
    const query = if (query_start) |idx| target[idx + 1 ..] else "";

    if (std.mem.eql(u8, path, "/") or std.mem.eql(u8, path, "/index.html")) {
        try respondFile(allocator, connection.stream, "static/index.html", "text/html; charset=utf-8");
    } else if (std.mem.eql(u8, path, "/style.css")) {
        try respondFile(allocator, connection.stream, "static/style.css", "text/css; charset=utf-8");
    } else if (std.mem.eql(u8, path, "/api/bytes")) {
        try respondBytesApi(allocator, connection.stream, query);
    } else {
        try writeResponse(connection.stream, "404 Not Found", "text/plain; charset=utf-8", "Not Found");
    }
}

// リクエストの1行目 "GET /path?query HTTP/1.1" からパス+クエリ部分だけを取り出す
fn requestPath(request: []const u8) ?[]const u8 {
    const line_end = std.mem.indexOfScalar(u8, request, '\r') orelse request.len;
    const request_line = request[0..line_end];

    const method_end = std.mem.indexOfScalar(u8, request_line, ' ') orelse return null;
    const rest = request_line[method_end + 1 ..];

    const path_end = std.mem.indexOfScalar(u8, rest, ' ') orelse rest.len;
    return rest[0..path_end];
}

// "count=42&type=u8" のようなクエリ文字列から指定キーの値を取り出す
fn queryValue(query: []const u8, key: []const u8) ?[]const u8 {
    var it = std.mem.splitScalar(u8, query, '&');
    while (it.next()) |pair| {
        const eq = std.mem.indexOfScalar(u8, pair, '=') orelse continue;
        const k = pair[0..eq];
        const v = pair[eq + 1 ..];
        if (std.mem.eql(u8, k, key)) return v;
    }
    return null;
}

const ByteView = struct {
    hex: []const u8,
    binary: []const u8,
};

// バイト列を "2A 00" のような16進表記と "00101010 00000000" のような2進表記にする。
// 「🔬 中身が見えるカウンター」機能の中核部分。
fn formatByteView(bytes: []const u8, hex_buf: []u8, bin_buf: []u8) !ByteView {
    var hex_len: usize = 0;
    var bin_len: usize = 0;

    for (bytes, 0..) |b, i| {
        if (i != 0) {
            hex_buf[hex_len] = ' ';
            hex_len += 1;
            bin_buf[bin_len] = ' ';
            bin_len += 1;
        }
        const hex_slice = try std.fmt.bufPrint(hex_buf[hex_len..], "{X:0>2}", .{b});
        hex_len += hex_slice.len;
        const bin_slice = try std.fmt.bufPrint(bin_buf[bin_len..], "{b:0>8}", .{b});
        bin_len += bin_slice.len;
    }

    return .{ .hex = hex_buf[0..hex_len], .binary = bin_buf[0..bin_len] };
}

fn respondBytesApi(allocator: std.mem.Allocator, stream: std.net.Stream, query: []const u8) !void {
    const count_str = queryValue(query, "count") orelse "0";
    const type_str = queryValue(query, "type") orelse "u32";

    const value = std.fmt.parseInt(u32, count_str, 10) catch {
        try writeResponse(
            stream,
            "400 Bad Request",
            "application/json; charset=utf-8",
            "{\"error\":\"count must be a non-negative integer\"}",
        );
        return;
    };

    var width: usize = 4;
    var max_value: u64 = std.math.maxInt(u32);
    var type_name: []const u8 = "u32";

    if (std.mem.eql(u8, type_str, "u8")) {
        width = 1;
        max_value = std.math.maxInt(u8);
        type_name = "u8";
    } else if (std.mem.eql(u8, type_str, "u16")) {
        width = 2;
        max_value = std.math.maxInt(u16);
        type_name = "u16";
    }

    const le_bytes = std.mem.toBytes(std.mem.nativeToLittle(u32, value));

    var hex_buf: [16]u8 = undefined;
    var bin_buf: [48]u8 = undefined;
    const view = try formatByteView(le_bytes[0..width], &hex_buf, &bin_buf);

    const fits = value <= max_value;

    const body = try std.fmt.allocPrint(
        allocator,
        "{{\"type\":\"{s}\",\"count\":{d},\"sizeBytes\":{d},\"bitWidth\":{d},\"hex\":\"{s}\",\"binary\":\"{s}\",\"maxValue\":{d},\"fits\":{}}}",
        .{ type_name, value, width, width * 8, view.hex, view.binary, max_value, fits },
    );
    defer allocator.free(body);

    try writeResponse(stream, "200 OK", "application/json; charset=utf-8", body);
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

test "requestPath extracts the root path" {
    const path = requestPath("GET / HTTP/1.1\r\nHost: localhost\r\n\r\n");
    try testing.expectEqualStrings("/", path.?);
}

test "requestPath extracts a nested path" {
    const path = requestPath("GET /style.css HTTP/1.1\r\n");
    try testing.expectEqualStrings("/style.css", path.?);
}

test "requestPath keeps the query string attached" {
    const path = requestPath("GET /api/bytes?count=42&type=u8 HTTP/1.1\r\n");
    try testing.expectEqualStrings("/api/bytes?count=42&type=u8", path.?);
}

test "requestPath returns null when there is no method/path separator" {
    try testing.expect(requestPath("garbage") == null);
}

test "queryValue finds a key in a query string" {
    try testing.expectEqualStrings("42", queryValue("count=42&type=u8", "count").?);
    try testing.expectEqualStrings("u8", queryValue("count=42&type=u8", "type").?);
}

test "queryValue returns null for a missing key" {
    try testing.expect(queryValue("count=42", "type") == null);
}

test "formatByteView renders hex and binary for a little-endian u32" {
    const value: u32 = 42;
    const bytes = std.mem.toBytes(std.mem.nativeToLittle(u32, value));

    var hex_buf: [16]u8 = undefined;
    var bin_buf: [48]u8 = undefined;
    const view = try formatByteView(&bytes, &hex_buf, &bin_buf);

    try testing.expectEqualStrings("2A 00 00 00", view.hex);
    try testing.expectEqualStrings("00101010 00000000 00000000 00000000", view.binary);
}

test "formatByteView renders a single byte for u8" {
    const value: u8 = 255;
    const bytes = [_]u8{value};

    var hex_buf: [16]u8 = undefined;
    var bin_buf: [48]u8 = undefined;
    const view = try formatByteView(&bytes, &hex_buf, &bin_buf);

    try testing.expectEqualStrings("FF", view.hex);
    try testing.expectEqualStrings("11111111", view.binary);
}
