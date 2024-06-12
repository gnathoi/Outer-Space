from flask import Flask, render_template_string, request

app = Flask(__name__)

# HTML template with a form
html_template = """
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Text Processor</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #f0f0f0;
            }
            .container {
                position: relative;
                width: 80%;
                text-align: center;
                background-color: #f0f8ff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
            }
            h1, h2 {
                color: #333;
            }
            input[type="text"], input[type="submit"] {
                box-sizing: border-box;
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ccc;
            }
            input[type="submit"] {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                background-color: #4682b4;
                color: #fff;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: #5f9ea0;
            }
            p {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                border: 1px solid #eee;
            }
            .toggle-button {
                position: absolute;
                top: 20px;
                right: 20px;
                width: 120px;
                height: 30px;
                background-color: #4682b4;
                border-radius: 15px;
                cursor: pointer;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 0;
                box-sizing: border-box;
                transition: background-color 0.3s;
                color: #fff;
                font-weight: bold;
            }
            .toggle-button.active {
                background-color: #5f9ea0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="toggle-button" id="toggleButton" onclick="toggleMode()">NL</div>
            <h1>Enter text to process</h1>
            <form method="post" id="textForm">
                <input type="hidden" name="mode" id="modeInput" value="NL">
                <input type="text" name="input_text" required>
                <input type="submit" value="Submit">
            </form>
            <h2>Result:</h2>
            <p>{{ result }}</p>
        </div>
        <script>
            function toggleMode() {
                var toggleButton = document.getElementById('toggleButton');
                var modeInput = document.getElementById('modeInput');
                toggleButton.classList.toggle('active');
                if (toggleButton.classList.contains('active')) {
                    modeInput.value = 'SPARQL';
                    toggleButton.textContent = 'SPARQL';
                } else {
                    modeInput.value = 'NL';
                    toggleButton.textContent = 'NL';
                }
            }
        </script>
    </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    if request.method == "POST":
        try:
            input_text = request.form["input_text"]
            mode = request.form["mode"]
            if mode == "NL":
                result = input_text[::-1]  # Reversing the input text
            elif mode == "SPARQL":
                result = " ".join(
                    "Z" + word[1:] if len(word) > 1 else "Z"
                    for word in input_text.split()
                )
        except KeyError as e:
            result = f"Error: Missing form field - {str(e)}"
    return render_template_string(html_template, result=result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
