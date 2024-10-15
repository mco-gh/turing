from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# Replace this with your OpenAI API key
OPENAI_API_KEY = 'your-openai-api-key'

# Store socket IDs for the human and the tester
human_socket_id = None
test_socket_id = None

@app.route('/')
def index():
    return render_template('index.html')  # Tester chat page

@app.route('/human')
def human():
    return render_template('human.html')  # Human chat page

# When a new connection is established
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
    global human_socket_id, test_socket_id

    # Relay the message to the human participant if connected
    if human_socket_id:
        socketio.emit('message', message, room=human_socket_id)

    # Fetch ChatGPT response and send it back to the tester
    chatgpt_response = get_chatgpt_response(message)
    socketio.emit('response', {'source': 'chatgpt', 'message': chatgpt_response}, room=test_socket_id)

# Handle incoming responses from the human
@socketio.on('human_response')
def handle_human_response(message):
    # Relay human response to the tester
    socketio.emit('response', {'source': 'human', 'message': message}, room=test_socket_id)

# Fetch response from OpenAI's API (ChatGPT)
def get_chatgpt_response(message):
    try:
        response = requests.post(
            'https://api.openai.com/v1/completions',
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}'},
            json={
                'model': 'text-davinci-003',
                'prompt': message,
                'max_tokens': 150
            }
        )
        response.raise_for_status()
        return response.json()['choices'][0]['text'].strip()
    except Exception as e:
        print(f"Error fetching ChatGPT response: {e}")
        return "Error: Unable to fetch response from ChatGPT."

if __name__ == '__main__':
    socketio.run(app, debug=True)
