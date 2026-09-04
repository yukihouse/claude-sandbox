using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc.Testing;

public class HomePageTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public HomePageTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetRoot_ReturnsCounterPage()
    {
        var response = await _client.GetAsync("/");

        response.EnsureSuccessStatusCode();
        Assert.Equal("text/html", response.Content.Headers.ContentType?.MediaType);

        var body = await response.Content.ReadAsStringAsync();
        Assert.Contains("カウンターデモ (C#版)", body);
    }

    [Fact]
    public async Task GetStyleCss_ReturnsCss()
    {
        var response = await _client.GetAsync("/style.css");

        response.EnsureSuccessStatusCode();
        Assert.Equal("text/css", response.Content.Headers.ContentType?.MediaType);
    }

    [Fact]
    public async Task GetUnknownPath_ReturnsNotFound()
    {
        var response = await _client.GetAsync("/unknown");

        Assert.Equal(System.Net.HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task PostClicksReset_ClearsStats()
    {
        await _client.PostAsync("/api/clicks", null);
        await _client.PostAsync("/api/clicks/reset", null);

        var stats = await _client.GetFromJsonAsync<JsonElement>("/api/stats");

        Assert.Equal(0, stats.GetProperty("totalClicks").GetInt32());
        Assert.Equal(JsonValueKind.Null, stats.GetProperty("averageIntervalMs").ValueKind);
    }

    [Fact]
    public async Task PostClicks_ThenGetStats_ReportsIntervals()
    {
        await _client.PostAsync("/api/clicks/reset", null);
        await _client.PostAsync("/api/clicks", null);
        await _client.PostAsync("/api/clicks", null);
        await _client.PostAsync("/api/clicks", null);

        var stats = await _client.GetFromJsonAsync<JsonElement>("/api/stats");

        Assert.Equal(3, stats.GetProperty("totalClicks").GetInt32());
        Assert.True(stats.GetProperty("averageIntervalMs").GetDouble() >= 0);
        Assert.True(stats.GetProperty("fastestIntervalMs").GetDouble() >= 0);
        Assert.True(stats.GetProperty("slowestIntervalMs").GetDouble() >= 0);
        Assert.Equal(2, stats.GetProperty("recentIntervalsMs").GetArrayLength());
    }
}
