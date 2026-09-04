import random

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# 「🎉 テンションが上がるカウンター」機能用の反応コメント集。
# 実際のLLMは使わず、節目の回数やクリック間隔に応じてランダムに選ぶだけの
# ルールベースだが、それっぽく反応しているように見せる。
MILESTONES = {1, 10, 25, 50, 100, 500, 1000}

MILESTONE_COMMENTS = [
    "🎉 {count}回達成！ここまで来たら止まりませんね",
    "✨ {count}回、なかなかやりますね！",
    "🏆 {count}回突破！お見事です",
]

FAST_COMMENTS = [
    "⚡ そんなに急いでどうしたんですか！？",
    "🔥 指が滑ってません？すごい勢いです",
    "💨 その連打スピード、尊敬します",
]

SLOW_COMMENTS = [
    "🐢 のんびりいきましょう",
    "☕ 一息ついてから、また押してくださいね",
    "🌙 マイペースなクリック、嫌いじゃないです",
]

NEUTRAL_COMMENTS = [
    "😊 いいペースですね",
    "👍 順調に増えてます",
    "🙂 その調子その調子",
]

FAST_THRESHOLD_MS = 300
SLOW_THRESHOLD_MS = 3000


def build_reaction(count: int, interval_ms: float | None) -> dict[str, str]:
    if count in MILESTONES:
        template = random.choice(MILESTONE_COMMENTS)
        return {"comment": template.format(count=count)}

    if interval_ms is not None and interval_ms < FAST_THRESHOLD_MS:
        return {"comment": random.choice(FAST_COMMENTS)}

    if interval_ms is not None and interval_ms > SLOW_THRESHOLD_MS:
        return {"comment": random.choice(SLOW_COMMENTS)}

    return {"comment": random.choice(NEUTRAL_COMMENTS)}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/react", methods=["POST"])
def react():
    data = request.get_json(silent=True) or {}
    count = data.get("count")
    interval_ms = data.get("intervalMs")

    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return jsonify({"error": "count must be a non-negative integer"}), 400

    if interval_ms is not None and not isinstance(interval_ms, (int, float)):
        return jsonify({"error": "intervalMs must be a number"}), 400

    return jsonify(build_reaction(count, interval_ms))


if __name__ == "__main__":
    app.run(port=5000)
