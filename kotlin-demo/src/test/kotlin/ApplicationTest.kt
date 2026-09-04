import io.ktor.client.request.get
import io.ktor.client.statement.bodyAsText
import io.ktor.http.HttpStatusCode
import io.ktor.server.testing.testApplication
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ApplicationTest {
    @Test
    fun homePageReturnsCounterMarkup() = testApplication {
        application { module() }

        val response = client.get("/")

        assertEquals(HttpStatusCode.OK, response.status)
        assertTrue(response.bodyAsText().contains("カウンターデモ (Kotlin版)"))
    }

    @Test
    fun staticStyleIsServed() = testApplication {
        application { module() }

        val response = client.get("/static/style.css")

        assertEquals(HttpStatusCode.OK, response.status)
    }

    @Test
    fun unknownPathReturnsNotFound() = testApplication {
        application { module() }

        val response = client.get("/unknown")

        assertEquals(HttpStatusCode.NotFound, response.status)
    }
}
