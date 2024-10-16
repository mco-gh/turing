from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from openai import OpenAI
import os
import requests
import time

SLEEP_TIME = 5
PORT = os.environ.get('PORT', 8080)

client = OpenAI()
app = Flask(__name__)
#app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# Store socket IDs for the tester and the human
test_socket_id = None
gpt_time_sent = None
human_socket_id = None
human_time_sent = None

@app.route('/')
def index():
    return render_template('index.html')  # Tester chat page

@app.route('/human')
def human():
    return render_template('human.html')  # Human chat page

# When a client registers 
@socketio.on('register')
def handle_register(role):
    global human_socket_id, test_socket_id
    if role == 'human':
        human_socket_id = request.sid
        print(f'Human registered with ID: {human_socket_id}')
    elif role == 'tester':
        test_socket_id = request.sid
        print(f'Tester registered with ID: {test_socket_id}')

# Handle incoming messages from the tester
@socketio.on('message')
def handle_message(message):
    global human_time_sent, gpt_time_sent, human_socket_id, test_socket_id

    # Relay the message to the human participant if connected
    if human_socket_id:
        human_time_sent = time.time()
        socketio.emit('message', message, room=human_socket_id)

    # Fetch ChatGPT response and send it back to the tester
    prompt = f"""
Respond with a one sentence answer to the following:
{message}"""
    gpt_time_sent = time.time()
    chatgpt_response = get_chatgpt_response(prompt)
    wait_time = max(0, SLEEP_TIME - (time.time() - gpt_time_sent))
    time.sleep(wait_time)
    socketio.emit('response', {'source': 'chatgpt', 'message': chatgpt_response.content}, room=test_socket_id)

# Handle incoming responses from the human
@socketio.on('human_response')
def handle_human_response(message):
    global human_time_sent
    wait_time = max(0, SLEEP_TIME - (time.time() - human_time_sent))
    time.sleep(wait_time)
    # Relay human response to the tester
    socketio.emit('response', {'source': 'human', 'message': message}, room=test_socket_id)
    # Relay human response to the human
    socketio.emit('message', message, room=human_socket_id)

# Fetch response from OpenAI's API (ChatGPT)
def get_chatgpt_response(message):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a normal human being of average intelligence and knowledge."},
                {"role": "user", "content": message},
            ]
        )
        return completion.choices[0].message
    except Exception as e:
        print(f"Error fetching ChatGPT response: {e}")
        return "Error: Unable to fetch response from ChatGPT."

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=PORT, debug=True, allow_unsafe_werkzeug=True)
