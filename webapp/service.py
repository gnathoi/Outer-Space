import io
import json
import os

import pandas as pd
import rdflib
import requests
from flask import Flask, render_template_string, request, send_file
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from pyparsing import ParseException

response = requests.get("http://httpbin.org/user-agent")
user_agent = json.loads(response.text)["user-agent"]
os.environ["USER_AGENT"] = user_agent.strip()

ollama = Ollama(base_url="http://localhost:11434", model="llama3")


def load_ttl_file(file_path):
    graph = rdflib.Graph()
    graph.parse(file_path, format="ttl")
    return graph


def perform_sparql_query(graph, query):
    """Perform a SPARQL query on the RDFLib graph."""
    return graph.query(query)


def display_query_results(results):
    """Display SPARQL query results as a pandas DataFrame."""
    # Transform the results into a list of dictionaries
    uri_to_remove = "http://www.owl-ontologies.com/"

    # Transform the results into a list of dictionaries, removing the specified URI part
    data = []
    for row in results:
        row_dict = {}
        for field in results.vars:
            value = str(row[field])
            # Remove the unwanted URI part if it's present
            if value.startswith(uri_to_remove):
                value = value[len(uri_to_remove) :]
            row_dict[str(field)] = value
        data.append(row_dict)

    # Create and display a DataFrame
    return pd.DataFrame(data)


def graph_to_documents(graph):
    documents = []
    for subj, pred, obj in graph:
        documents.append(Document(page_content=f"{subj} {pred} {obj}"))
    return documents


ttl_file = "DamageInstances.ttl"  # Change this to your Turtle file path
ont_ttl_file = "DamageLocationOntology.ttl"
graph = load_ttl_file(ttl_file)
# graph_ont = load_ttl_file(ont_ttl_file)

rdf_text_data = graph_to_documents(graph)  # + graph_to_documents(graph_ont)

# Split text data for embeddings
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
all_splits = text_splitter.split_documents(rdf_text_data)

oembed = OllamaEmbeddings(base_url="http://localhost:11434", model="nomic-embed-text")
vectorstore = Chroma.from_documents(documents=all_splits, embedding=oembed)

app = Flask(__name__)

# HTML template with a form
html_template = """
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>RAGdol</title>
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
                max-width: 900px;
                background-color: #ffffff;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
            }
            textarea, input[type="submit"] {
                box-sizing: border-box;
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ccc;
                font-size: 16px;
            }
            textarea {
                height: 200px;
                resize: horizontal;
                overflow: auto;
            }
            input[type="submit"] {
                padding: 12px 20px;
                border: none;
                border-radius: 5px;
                background-color: #4682b4;
                color: #fff;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: background-color 0.3s;
            }
            input[type="submit"]:hover {
                background-color: #5f9ea0;
            }
            p {
                padding: 20px;
                border-radius: 5px;
                border: 1px solid #eee;
                text-align: left;
                font-size: 16px;
                background-color: #f8f9fa;
            }
            .toggle-button {
                position: absolute;
                top: 20px;
                right: 20px;
                width: 120px;
                height: 40px;
                background-color: #4682b4;
                border-radius: 20px;
                cursor: pointer;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 0;
                box-sizing: border-box;
                transition: background-color 0.3s;
                color: #fff;
                font-weight: bold;
                font-size: 16px;
            }
            .toggle-button.active {
                background-color: #5f9ea0;
            }
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            th {
                padding-top: 12px;
                padding-bottom: 12px;
                text-align: left;
                background-color: #4CAF50;
                color: white;
            }
            .scrollable-div {
                max-height: 500px;
                overflow-y: auto;
                margin-top: 20px;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: left;
            }
            .download-button {
                padding: 12px 20px;
                border: none;
                border-radius: 5px;
                background-color: #4682b4;
                color: #fff;
                cursor: pointer;
                margin-top: 10px;
                font-size: 16px;
                font-weight: bold;
                transition: background-color 0.3s;
            }
            .download-button:hover {
                background-color: #5f9ea0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="toggle-button" id="toggleButton" onclick="toggleMode()">NL</div>
            <h1>RAGdol</h1>
            <form method="post" id="textForm">
                <input type="hidden" name="mode" id="modeInput" value="NL">
                <textarea name="input_text" required></textarea>
                <input type="submit" value="Submit">
            </form>
            <div class="scrollable-div">
                <p><i>{{ question }}</i></p>
                <div>{{ result|safe }}</div>
                {% if result %}
                <form method="post" action="/download">
                    <input type="hidden" name="result_data" value="{{ result_data }}">
                    <input type="hidden" name="result_type" value="{{ result_type }}">
                    <button type="submit" class="download-button">Download Result</button>
                </form>
                {% endif %}
            </div>
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
                localStorage.setItem('toggleButtonState', modeInput.value);
            }
            window.onload = function() {
                var toggleButton = document.getElementById('toggleButton');
                var modeInput = document.getElementById('modeInput');
                var toggleButtonState = localStorage.getItem('toggleButtonState');
                if (toggleButtonState === 'SPARQL') {
                    toggleButton.classList.add('active');
                    modeInput.value = 'SPARQL';
                    toggleButton.textContent = 'SPARQL';
                } else {
                    toggleButton.classList.remove('active');
                    modeInput.value = 'NL';
                    toggleButton.textContent = 'NL';
                }
            }
            document.getElementById('textForm').onsubmit = function() {
                setTimeout(function() {
                    window.scrollTo(0, 0);
                }, 100);
            };
        </script>
    </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    question = ""
    result_data = ""
    result_type = "text"
    if request.method == "POST":
        try:
            input_text = request.form["input_text"]
            mode = request.form["mode"]
            question = input_text
            if mode == "NL":
                # Use the RetrievalQA class and the similarity_search method
                docs = vectorstore.similarity_search(input_text)
                qachain = RetrievalQA.from_chain_type(
                    ollama, retriever=vectorstore.as_retriever()
                )
                res = qachain.invoke({"query": input_text})
                result = res["result"]
                result_data = result
                result_type = "text"
            elif mode == "SPARQL":
                try:
                    # Perform the SPARQL query and display the results as a DataFrame
                    query_results = perform_sparql_query(graph, input_text)
                    df = display_query_results(query_results)
                    result = df.to_html(
                        classes="dataframe"
                    )  # Convert DataFrame to HTML
                    result_data = df.to_csv(index=False)
                    result_type = "dataframe"
                except ParseException:
                    result = "Error: Invalid SPARQL query"
                    result_data = result
                    result_type = "text"
        except KeyError as e:
            result = f"Error: Missing form field - {str(e)}"
            result_data = result
            result_type = "text"
    return render_template_string(
        html_template,
        result=result,
        question=question,
        result_data=result_data,
        result_type=result_type,
    )


@app.route("/download", methods=["POST"])
def download():
    result_data = request.form["result_data"]
    result_type = request.form["result_type"]
    if result_type == "dataframe":
        output = io.StringIO(result_data)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name="result.csv",
        )
    else:
        return send_file(
            io.BytesIO(result_data.encode()),
            mimetype="text/plain",
            as_attachment=True,
            download_name="result.txt",
        )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
