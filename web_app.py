from flask import Flask, render_template, request
from dotenv import load_dotenv
from agent import LocalAIAgent

load_dotenv()
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    artist_name = ""
    result_text = ""
    error = None

    if request.method == "POST":
        artist_name = request.form.get("artist", "").strip()
        if not artist_name:
            error = "請輸入歌手名稱。"
        else:
            try:
                agent = LocalAIAgent()
                result_text = agent.search_artist_songs(artist_name)
            except Exception as exc:
                error = str(exc)

    return render_template(
        "index.html",
        artist=artist_name,
        result_text=result_text,
        error=error,
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
