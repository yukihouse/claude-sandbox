import gradio as gr


def compute_increment(count: int) -> tuple[int, str]:
    new_count = count + 1
    return new_count, str(new_count)


def compute_reset(_count: int) -> tuple[int, str]:
    return 0, "0"


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="カウンターデモ (Python版 / Gradio)") as demo:
        gr.Markdown("# カウンターデモ (Python版 / Gradio)")

        count = gr.State(0)
        count_display = gr.Markdown("0", elem_id="count")

        with gr.Row():
            increment_btn = gr.Button("+1", elem_id="increment")
            reset_btn = gr.Button("リセット", elem_id="reset")

        gr.HTML('<nav><a href="http://localhost:8080/">ホームへ戻る</a></nav>')

        increment_btn.click(
            compute_increment, inputs=count, outputs=[count, count_display]
        )
        reset_btn.click(compute_reset, inputs=count, outputs=[count, count_display])

    return demo


demo = build_demo()

if __name__ == "__main__":
    demo.launch(server_port=5007)
