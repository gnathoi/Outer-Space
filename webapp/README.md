# Using ragdol.py

## Install Ollama

Follow the instructions for installing [Ollama](https://github.com/ollama/ollama).

For linux users simply use:
```
curl -fsSL https://ollama.com/install.sh | sh
```

Once installed pull the relevant models and embedder.
```
ollama pull llama3
ollama pull nomic-embed-text
```

Then run:
```
ollama serve
```

And go to a new terminal.

## Create a virtual environment

In the new terminal create a python3.10 virtual environment:
```
python3.10 -m venv myenv
```

Activate it:
```
source myenv/bin/activate
```

Navigate to the webapp directory and run:
```
pip install -r requirements.txt
```

## Launch the flask app

```
python ragdol.py
```

In the code for ragdol.py change the ttl_file variable to the path for your ttl file to run RAG and SPARQL queries on your own graphs.

To view and interact with it go to your browser and go to:
```
localhost:5000
```
