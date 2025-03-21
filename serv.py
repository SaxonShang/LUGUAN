from flask import Flask, render_template

app = Flask(__name__,static_folder='static')

@app.route('/')
def home():
    return render_template('index.html')  # 使用 render_template 查找 templates/index.html

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)