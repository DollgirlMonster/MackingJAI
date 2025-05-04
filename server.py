from flask import Flask, request, jsonify
import subprocess
from threading import Event
import re

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
    "GPT-4",
    "GPT-4o mini",
    "o4-mini-high",
    "o4-mini",
    "o3",
    "GPT-4.5",
    "GPT-4o"
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
    
    # Try to match with one of our standard model names
    model_name = next((m for m in models if model_name.lower() == m.lower()), model_name)
    
    if model_name == "o1-pro":
        print("o1-pro is not supported, using o3 instead")
        model_name = "o3"
    elif model_name == "gpt-4.1":
        print("gpt-4.1 is not supported, using gpt-4 instead")
        model_name = "GPT-4"
    elif model_name == "gpt-4.1-mini":
        print("gpt-4.1-mini is not supported, using gpt-4o instead")
        model_name = "GPT-4o"
    elif model_name == "gpt-4.1-nano":
        print("gpt-4.1-nano is not supported, using gpt-4o mini instead")
        model_name = "GPT-4o mini"
    print(f"Model name: {model_name}")
    assert model_name in models, f"Model {model_name} is not supported.\n"
    return model_name

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