const std = @import("std");

const PORT = 5005;

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

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
    const path = requestPath(buf[0..n]) orelse "/";

    if (std.mem.eql(u8, path, "/") or std.mem.eql(u8, path, "/index.html")) {
        try respondFile(allocator, connection.stream, "static/index.html", "text/html; charset=utf-8");
    } else if (std.mem.eql(u8, path, "/style.css")) {
        try respondFile(allocator, connection.stream, "static/style.css", "text/css; charset=utf-8");
    } else {
        try writeResponse(connection.stream, "404 Not Found", "text/plain; charset=utf-8", "Not Found");
    }
}

// リクエストの1行目 "GET /path HTTP/1.1" からパス部分だけを取り出す
fn requestPath(request: []const u8) ?[]const u8 {
    const line_end = std.mem.indexOfScalar(u8, request, '\r') orelse request.len;
    const request_line = request[0..line_end];

    const method_end = std.mem.indexOfScalar(u8, request_line, ' ') orelse return null;
    const rest = request_line[method_end + 1 ..];

    const path_end = std.mem.indexOfScalar(u8, rest, ' ') orelse rest.len;
    return rest[0..path_end];
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
