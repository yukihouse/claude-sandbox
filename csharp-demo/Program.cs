var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var clickLog = new ClickLog();

app.UseDefaultFiles();
app.UseStaticFiles();

app.MapPost("/api/clicks", () =>
{
    clickLog.Record();
    return Results.Ok();
});

app.MapPost("/api/clicks/reset", () =>
{
    clickLog.Clear();
    return Results.Ok();
});

app.MapGet("/api/stats", () => Results.Ok(clickLog.ComputeStats()));

app.Run("http://localhost:5003");

public partial class Program { }

// +1ボタンが押された時刻を記録し、LINQでクリック間隔の統計を計算する
// 「📊 クリック統計」機能のためのクラス。
class ClickLog
{
    private readonly List<DateTimeOffset> _timestamps = [];
    private readonly object _lock = new();

    public void Record()
    {
        lock (_lock)
        {
            _timestamps.Add(DateTimeOffset.UtcNow);
        }
    }

    public void Clear()
    {
        lock (_lock)
        {
            _timestamps.Clear();
        }
    }

    public ClickStats ComputeStats()
    {
        DateTimeOffset[] snapshot;
        lock (_lock)
        {
            snapshot = [.. _timestamps];
        }

        var intervalsMs = snapshot
            .Zip(snapshot.Skip(1), (previous, current) => (current - previous).TotalMilliseconds)
            .ToArray();

        return new ClickStats(
            TotalClicks: snapshot.Length,
            AverageIntervalMs: intervalsMs.Length > 0 ? Math.Round(intervalsMs.Average(), 1) : null,
            FastestIntervalMs: intervalsMs.Length > 0 ? Math.Round(intervalsMs.Min(), 1) : null,
            SlowestIntervalMs: intervalsMs.Length > 0 ? Math.Round(intervalsMs.Max(), 1) : null,
            RecentIntervalsMs: [.. intervalsMs.TakeLast(5).Select(ms => Math.Round(ms, 1))]
        );
    }
}

record ClickStats(
    int TotalClicks,
    double? AverageIntervalMs,
    double? FastestIntervalMs,
    double? SlowestIntervalMs,
    double[] RecentIntervalsMs
);
