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
}
