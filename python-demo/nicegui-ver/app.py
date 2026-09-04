from nicegui import ui


def compute_increment(count: int) -> int:
    return count + 1


def compute_reset(_count: int) -> int:
    return 0


@ui.page("/")
def index() -> None:
    count = {"value": 0}

    ui.label("カウンターデモ (Python版 / NiceGUI)").classes("text-2xl font-bold")
    count_label = ui.label(str(count["value"])).classes(
        "text-6xl font-mono"
    )

    def on_increment() -> None:
        count["value"] = compute_increment(count["value"])
        count_label.set_text(str(count["value"]))

    def on_reset() -> None:
        count["value"] = compute_reset(count["value"])
        count_label.set_text(str(count["value"]))

    with ui.row():
        ui.button("+1", on_click=on_increment)
        ui.button("リセット", on_click=on_reset)

    ui.link("ホームへ戻る", "http://localhost:8080/")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=5008, title="カウンターデモ (Python版 / NiceGUI)")
