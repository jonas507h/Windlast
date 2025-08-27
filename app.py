from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        try:
            a = float(request.form.get("a", 0))
            b = float(request.form.get("b", 0))
            result = a + b
        except ValueError:
            result = "Ungültige Eingabe"
    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
