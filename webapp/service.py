import json
import os

import pandas as pd
import rdflib
import requests
from flask import Flask, render_template_string, request
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


ttl_file = "MaintenanceBridgeModel.ttl"  # Change this to your Turtle file path
graph = load_ttl_file(ttl_file)


def graph_to_documents(graph):
    documents = []
    for subj, pred, obj in graph:
        documents.append(Document(page_content=f"{subj} {pred} {obj}"))
    return documents


rdf_text_data = graph_to_documents(graph)

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
                text-align: center;
                background-color: #f0f8ff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
            }
            h1, h2 {
                color: #333;
            }
            textarea, input[type="submit"] {
                box-sizing: border-box;
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ccc;
            }
            textarea {
                height: 200px;  /* Adjust the height as needed */
                resize: horizontal;  /* Allow horizontal resizing */
                overflow: auto;  /* Add a scrollbar if the text overflows */
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
            /* DataFrame styling */
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
            /* Add a style for the scrollable div */
            .scrollable-div {
                max-height: 500px;
                overflow-y: auto;
                margin-top: 20px;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
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
            <!-- Wrap the result in a scrollable div -->
            <div class="scrollable-div">
                <div>{{ result|safe }}</div>
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
                // Save the state of the toggle button
                localStorage.setItem('toggleButtonState', modeInput.value);
            }
            // Load the state of the toggle button
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
                // Scroll to the top of the page after form submission
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
    if request.method == "POST":
        try:
            input_text = request.form["input_text"]
            mode = request.form["mode"]
            if mode == "NL":
                # Use the RetrievalQA class and the similarity_search method
                docs = vectorstore.similarity_search(input_text)
                qachain = RetrievalQA.from_chain_type(
                    ollama, retriever=vectorstore.as_retriever()
                )
                res = qachain.invoke({"query": input_text})
                result = res["result"]
            elif mode == "SPARQL":
                try:
                    # Perform the SPARQL query and display the results as a DataFrame
                    query_results = perform_sparql_query(graph, input_text)
                    df = display_query_results(query_results)
                    result = df.to_html(
                        classes="dataframe"
                    )  # Convert DataFrame to HTML
                except ParseException:
                    result = "Error: Invalid SPARQL query"
        except KeyError as e:
            result = f"Error: Missing form field - {str(e)}"
    return render_template_string(html_template, result=result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
