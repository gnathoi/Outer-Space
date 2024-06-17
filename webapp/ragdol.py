#!/usr/bin/env python3

import json
import os

import pandas as pd
import rdflib
import requests
from flask import Flask, Response, render_template_string, request
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

ttl_file = "MaintenanceBridgeModel.ttl"  # Change this to your Turtle file path


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

    df = pd.DataFrame(data)
    return df


# Function to create a document from the Turtle file directly
def ttl_file_to_document(file_path: str) -> Document:
    with open(file_path, encoding="utf-8") as file:
        content = file.read()
    return Document(page_content=content)


# Load RDF data
graph = load_ttl_file(ttl_file)
rdf_text_document = ttl_file_to_document(ttl_file)

# Split text data for embeddings
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
all_splits = text_splitter.split_documents([rdf_text_document])

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
            @import url('https://fonts.googleapis.com/css2?family=Charter:wght@400;700&display=swap');
            body {
                font-family: 'Charter', serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #f0f0f0;
                transition: background-color 0.3s, color 0.3s;
            }
            .container {
                position: relative;
                width: 80%;
                max-width: 900px;
                background-color: #ffffff;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                height: 90%;
                transition: background-color 0.3s, color 0.3s;
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .header .toggle-button, .header .dark-mode-button {
                margin-left: 10px;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
            }
            .dark-mode h1 {
                color: #d3d3d3;
            }
            textarea {
                box-sizing: border-box;
                width: calc(100% - 60px); /* Account for button width and margin */
                padding: 12px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ccc;
                font-size: 16px;
                transition: background-color 0.3s, color 0.3s, border-color 0.3s;
                position: relative;
            }
            .stop-button {
                position: absolute;
                bottom: 15px;
                right: 15px;
                background-color: white;
                border: 2px solid black;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                cursor: pointer;
                display: flex;
                justify-content: center;
                align-items: center;
                transition: background-color 0.3s;
            }
            .stop-button::before {
                content: "▶";
                color: black;
                font-size: 20px;
            }
            .stop-button.thinking::before {
                content: "■";
                color: black;
                font-size: 20px;
            }
            .thinking {
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 10px rgba(70, 130, 180, 0.7);
                }
                50% {
                    box-shadow: 0 0 20px rgba(70, 130, 180, 1);
                }
                100% {
                    box-shadow: 0 0 10px rgba(70, 130, 180, 0.7);
                }
            }
            p {
                padding: 20px;
                border-radius: 5px;
                border: 1px solid #eee;
                text-align: left;
                font-size: 16px;
                background-color: #f8f9fa;
                transition: background-color 0.3s, color 0.3s, border-color 0.3s;
            }
            .toggle-button {
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
            .dark-mode-button {
                width: 40px;
                height: 40px;
                background-color: #333;
                border-radius: 20px;
                cursor: pointer;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 0;
                box-sizing: border-box;
                transition: background-color 0.3s, color 0.3s;
                color: #fff;
                font-size: 24px;
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
                flex-grow: 1;
                overflow-y: auto;
                margin-top: 20px;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: left;
                transition: background-color 0.3s, color 0.3s, border-color 0.3s;
                display: flex;
                flex-direction: column-reverse; /* New messages appear at the top */
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
            .dark-mode {
                background-color: #121212;
                color: #ffffff;
            }
            .dark-mode .container {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            .dark-mode textarea, .dark-mode p, .dark-mode .scrollable-div {
                background-color: #333;
                color: #ffffff;
                border-color: #555;
            }
            .dark-mode .stop-button {
                background-color: white;
                border-color: black;
            }
            .chat-container {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .chat-message {
                display: flex;
                flex-direction: column;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #fff;
            }
            .chat-message.user {
                align-self: flex-end;
                background-color: #e0f7fa;
            }
            .chat-message.bot {
                align-self: flex-start;
                background-color: #fce4ec;
            }
            .footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>RAGdol</h1>
                <div>
                    <div class="toggle-button" id="toggleButton" onclick="toggleMode()">NL</div>
                    <div class="dark-mode-button" id="darkModeButton" onclick="toggleDarkMode()">
                        <span class="icon">🌜</span>
                    </div>
                </div>
            </div>
            <div class="scrollable-div chat-container" id="chatContainer"></div>
            <div class="footer">
                <form id="textForm" style="width: 100%;">
                    <input type="hidden" name="mode" id="modeInput" value="NL">
                    <div style="position: relative;">
                        <textarea name="input_text" id="inputText" required></textarea>
                        <button type="button" class="stop-button" id="stopButton"></button>
                    </div>
                </form>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
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
            function toggleDarkMode() {
                var darkModeButton = document.getElementById('darkModeButton');
                document.body.classList.toggle('dark-mode');
                if (document.body.classList.contains('dark-mode')) {
                    darkModeButton.innerHTML = '<span class="icon">🌞</span>';
                } else {
                    darkModeButton.innerHTML = '<span class="icon">🌜</span>';
                }
                localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
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
                if (localStorage.getItem('darkMode') === 'true') {
                    document.body.classList.add('dark-mode');
                    document.getElementById('darkModeButton').innerHTML = '<span class="icon">🌞</span>';
                }
            }
            document.getElementById('stopButton').onclick = function() {
                var inputText = document.getElementById('inputText');
                if (inputText.classList.contains('thinking')) {
                    inputText.classList.remove('thinking');
                    this.classList.remove('thinking');
                    inputText.value = '';
                    inputText.focus();
                    document.getElementById('textForm').reset();
                } else {
                    startRequest();
                    inputText.classList.add('thinking');
                    this.classList.add('thinking');
                }
            };
            function startRequest() {
                var form = document.getElementById('textForm');
                var formData = new FormData(form);
                var eventSource = new EventSource('/stream?' + new URLSearchParams(formData).toString());

                eventSource.onmessage = function(event) {
                    var chatContainer = document.getElementById('chatContainer');
                    var newMessage = document.createElement('div');
                    newMessage.classList.add('chat-message', 'bot');
                    newMessage.innerHTML = '<p>' + event.data + '</p>';
                    chatContainer.prepend(newMessage); // New messages at the top
                };

                eventSource.onerror = function() {
                    eventSource.close();
                    var inputText = document.getElementById('inputText');
                    inputText.classList.remove('thinking');
                    var stopButton = document.getElementById('stopButton');
                    stopButton.classList.remove('thinking');
                };
            }
        </script>
    </body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(html_template)


@app.route("/stream", methods=["GET"])
def stream():
    mode = request.args.get("mode")
    input_text = request.args.get("input_text")

    def generate_nl_response():
        docs = vectorstore.similarity_search(input_text)
        qachain = RetrievalQA.from_chain_type(
            ollama, retriever=vectorstore.as_retriever()
        )
        res = qachain.invoke({"query": input_text})
        for line in res["result"].splitlines():
            yield f"data: {line}\n\n"

    if mode == "NL":
        return Response(generate_nl_response(), mimetype="text/event-stream")
    elif mode == "SPARQL":
        try:
            query_results = perform_sparql_query(graph, input_text)
            df = display_query_results(query_results)
            result = df.to_html(classes="dataframe")
            return Response(f"data: {result}\n\n", mimetype="text/event-stream")
        except ParseException:
            return Response(
                "data: Error: Invalid SPARQL query\n\n", mimetype="text/event-stream"
            )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
