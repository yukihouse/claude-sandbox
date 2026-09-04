import io.ktor.http.ContentType
import io.ktor.server.application.Application
import io.ktor.server.engine.embeddedServer
import io.ktor.server.http.content.staticResources
import io.ktor.server.netty.Netty
import io.ktor.server.response.respondText
import io.ktor.server.routing.get
import io.ktor.server.routing.routing

const val PORT = 5007

fun main() {
    println("Listening on http://localhost:$PORT")
    embeddedServer(Netty, port = PORT, host = "0.0.0.0", module = Application::module)
        .start(wait = true)
}

fun Application.module() {
    routing {
        staticResources("/static", "static")

        get("/") {
            call.respondText(indexHtml(), ContentType.Text.Html)
        }
    }
}

private fun indexHtml(): String =
    object {}.javaClass.classLoader
        .getResourceAsStream("templates/index.html")!!
        .bufferedReader()
        .use { it.readText() }
