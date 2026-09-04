import io.ktor.http.ContentType
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.http.content.staticResources
import io.ktor.server.netty.Netty
import io.ktor.server.response.respondText
import io.ktor.server.routing.get
import io.ktor.server.routing.routing
import io.ktor.server.sse.SSE
import io.ktor.server.sse.ServerSSESession
import io.ktor.server.sse.sse
import io.ktor.sse.ServerSentEvent
import kotlinx.coroutines.delay

const val PORT = 5009

// 「🚀 コルーチンオートパイロット」で自動インクリメントする回数と間隔。
const val AUTOPILOT_TICKS = 8
const val AUTOPILOT_DELAY_MS = 250L

fun main() {
    println("Listening on http://localhost:$PORT")
    embeddedServer(Netty, port = PORT, host = "0.0.0.0", module = Application::module)
        .start(wait = true)
}

fun Application.module() {
    install(SSE)

    routing {
        staticResources("/static", "static")

        get("/") {
            call.respondText(indexHtml(), ContentType.Text.Html)
        }

        sse("/api/autopilot") {
            runAutopilot()
        }
    }
}

// coroutineのdelay（スレッドをブロックしない待機）でサーバー側が自動的にカウントアップし、
// Server-Sent Eventsでブラウザにリアルタイム配信する。
private suspend fun ServerSSESession.runAutopilot() {
    for (count in 1..AUTOPILOT_TICKS) {
        delay(AUTOPILOT_DELAY_MS)
        send(ServerSentEvent(data = count.toString()))
    }
    send(ServerSentEvent(data = "done", event = "done"))
}

private fun indexHtml(): String =
    object {}.javaClass.classLoader
        .getResourceAsStream("templates/index.html")!!
        .bufferedReader()
        .use { it.readText() }
