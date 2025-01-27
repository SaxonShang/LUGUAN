from flask import Flask, render_template, request
import database_manager

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/set_style", methods=["POST"])
def set_style():
    style = request.form["style"]
    database_manager.save_style(style)
    return "风格已更新！"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
