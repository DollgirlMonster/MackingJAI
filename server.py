from flask import Flask, request, jsonify, Response
import subprocess
from threading import Event
import re
import json
import time

VERSION = "0.4"

# Global event flag
message_ready = Event()

# Default values
default_prompt = "hi, what is 1 + 1"
default_model = "GPT-4o"

# Store prompt and model values
stored_prompt = default_prompt
stored_model = default_model
stored_message = ""

models = [
    "o4-mini-high",
    "o4-mini",
    "o3",
    "GPT-4.5",
    "GPT-4o",
    "GPT-4.1",
    "GPT-4.1-mini",
    "apple_local",
    "apple_cloud"
]

# Flask app
app = Flask(__name__)

def model_handler(model_name):
    """
    Function to handle model names and return a standardized version.
    """
    # Check if the model name is in the list of supported models
    # If the model name contains a snapshot, remove it
    model_name = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', model_name)
    # strip :
    model_name = model_name.split(":")[0]
    
    # Try to match with one of our standard model names
    model_name = next((m for m in models if model_name.lower() == m.lower()), model_name)
    
    if model_name == "o1-pro":
        print("o1-pro is not supported, using o3 instead")
        model_name = "o3"
    elif model_name == "gpt-4.1-nano":
        print("gpt-4.1-nano is not supported, using gpt-4o mini instead")
        model_name = "GPT-4o mini"
    assert model_name in models, f"Model {model_name} is not supported.\n"
    return model_name

# OpenAI API
@app.route('/v1/chat/completions', methods=['POST'])
def prompt_model():
    global stored_prompt, stored_model, stored_message
    message_ready.clear()
    
    if request.method == 'POST':
        data = request.get_json()        
        # Extract the user's prompt from the OpenAI‑style messages list
        messages = data.get('messages', [])
        # Build conversation history as prompt for the model
        if isinstance(messages, list) and messages:
            formatted_history = []
            for m in messages:
                role = m.get('role')
                content = m.get('content', "")
                if role == "system":
                    formatted_history.append(f"System: {content}")
                elif role == "user":
                    formatted_history.append(f"User: {content}")
                elif role == "assistant":
                    formatted_history.append(f"Assistant: {content}")
                else:
                    formatted_history.append(f"{role.capitalize()}: {content}")
            stored_prompt = "\n".join(formatted_history)
        else:
            stored_prompt = default_prompt
        
        # Handling model names
        stored_model = data.get('model', default_model)
        stored_model = model_handler(stored_model)
        
        stored_message = ""  # will be filled later by /internal POST
        
        subprocess.Popen(["shortcuts", "run", "MackingJAI"])
        message_ready.wait()
        
        stream = data.get('stream', False)
        
        if not stream:
            response_payload = {
                "id": "chatcmpl-local-001",
                "object": "chat.completion",
                "created": 0,
                "model": stored_model,
                "prompt": stored_prompt,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": stored_message
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                # Generic signal that processing is done
                "finish_signal": True
            }
            response = jsonify(response_payload)
            # Add a generic header to signal completion
            response.headers['X-Chat-Complete'] = 'true'
            return response
        else:
            # Streaming: yield chunks of the message
            def generate_stream():
                import uuid
                now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                chunk_size = 8  # characters per chunk
                content = stored_message or ""
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i+chunk_size]
                    obj = {
                        "id": "chatcmpl-local-001",
                        "object": "chat.completion.chunk",
                        "created": 0,
                        "model": stored_model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "role": "assistant",
                                    "content": chunk
                                },
                                "finish_reason": None
                            }
                        ]
                    }
                    yield f"data: {json.dumps(obj)}\n\n"
                    time.sleep(0.001)
                # Final chunk with finish_reason and usage
                obj = {
                    "id": "chatcmpl-local-001",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": stored_model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": ""
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                yield f"data: {json.dumps(obj)}\n\n"
            return Response(generate_stream(), mimetype='application/x-ndjson')

@app.route('/v1/models', methods=['GET'])
def list_models():
    """
    Return a list of supported models in the OpenAI API format.
    """
    return jsonify({
        "data": [
            {"id": m, "object": "model"} for m in models
        ]
    })

# Ollama API
@app.route('/api/chat', methods=['POST'])
def prompt_model_ollama():
    global stored_prompt, stored_model, stored_message
    message_ready.clear()
    
    if request.method == 'POST':
        try:
            data = request.get_json(force=True)
        except Exception:
            # Fallback: try to parse raw data as JSON
            data = None
            if request.data:
                try:
                    data = json.loads(request.data.decode('utf-8'))
                except Exception:
                    data = {}
        if not data:
            data = {}
        
        # Extract the user's prompt from the OpenAI‑style messages list
        messages = data.get('messages', [])
        # Build conversation history as prompt for the model
        if isinstance(messages, list) and messages:
            formatted_history = []
            for m in messages:
                role = m.get('role')
                content = m.get('content', "")
                if role == "system":
                    formatted_history.append(f"System: {content}")
                elif role == "user":
                    formatted_history.append(f"User: {content}")
                elif role == "assistant":
                    formatted_history.append(f"Assistant: {content}")
                else:
                    formatted_history.append(f"{role.capitalize()}: {content}")
            stored_prompt = "\n".join(formatted_history)
        else:
            stored_prompt = default_prompt
        
        # Handling model names
        stored_model = data.get('model', default_model)
        stored_model = model_handler(stored_model)
        
        stored_message = ""  # will be filled later by /internal POST
        
        subprocess.Popen(["shortcuts", "run", "MackingJAI"])
        message_ready.wait()
        
        stream = data.get('stream', True)
        
        if not stream:
            # Non-streaming: return the whole message at once
            response_payload = {
                "model": stored_model,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "message": {
                    "role": "assistant",
                    "content": stored_message
                },
                "done_reason": "stop",
                "done": True,
                "total_duration": 0,
                "load_duration": 0,
                "prompt_eval_count": 0,
                "prompt_eval_duration": 0,
                "eval_count": 0,
                "eval_duration": 0
            }
            return jsonify(response_payload)
        else:
            # Streaming: yield chunks of the message
            def generate_stream():
                import uuid
                now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                chunk_size = 8  # characters per chunk
                content = stored_message or ""
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i+chunk_size]
                    obj = {
                        "model": stored_model,
                        "created_at": now,
                        "message": {
                            "role": "assistant",
                            "content": chunk
                        },
                        "done": False
                    }
                    yield json.dumps(obj) + '\n'
                    time.sleep(0.001)
                # Final chunk with done: true
                obj = {
                    "model": stored_model,
                    "created_at": now,
                    "message": {
                        "role": "assistant",
                        "content": ""
                    },
                    "done_reason": "stop",
                    "done": True,
                    "total_duration": 0,
                    "load_duration": 0,
                    "prompt_eval_count": 0,
                    "prompt_eval_duration": 0,
                    "eval_count": 0,
                    "eval_duration": 0
                }
                yield json.dumps(obj) + '\n'
            return Response(generate_stream(), mimetype='application/x-ndjson')

@app.route('/api/tags', methods=['GET'])
@app.route('/api/ps', methods=['GET'])
def list_models_ollama():
    """
    Return a list of supported models in the OpenAI API format.
    """
    return jsonify({
        "models": [
            {"name":m, "model": m + ":latest" , "size": 1, "digest": "", "modified_at": "2025-01-01T11:15:24.832444301+03:00"} for m in models
        ]
    })

@app.route('/api/show', methods=['POST'])
def show_model():
    data = request.get_json()
    model_name = data.get('model', default_model)
    model_name = model_handler(model_name)
    with open("api_show.json") as f:
        json_format = json.load(f)
    # Recursively replace all 'modelname_placeholder' with model_name
    def replace_placeholders(obj):
        if isinstance(obj, dict):
            return {k: replace_placeholders(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_placeholders(i) for i in obj]
        elif obj == "modelname_placeholder":
            return model_name
        else:
            return obj
    json_format = replace_placeholders(json_format)
    return jsonify(json_format)

@app.route('/api/version', methods=['GET'])
def version():
    return jsonify({"version": VERSION})

@app.route('/internal', methods=['GET', 'POST'])
def internal():
    global stored_prompt, stored_model, stored_message
    
    if request.method == 'GET':
        return jsonify({
            "prompt": stored_prompt,
            "model": stored_model
        })
    else:  # POST
        data = request.get_json()
        stored_message = data.get('message', "")
        message_ready.set()
        return jsonify({"status": "ok"})

def run_server():
    app.run(host="0.0.0.0", debug=False, threaded=True, port=11435, use_reloader=False)

if __name__ == '__main__':
    run_server()
