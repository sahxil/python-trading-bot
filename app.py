# app.py
from flask import Flask, render_template
from flask_socketio import SocketIO

# Initialize the Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def dashboard():
    """Serves the main dashboard HTML page."""
    return render_template('dashboard.html')

if __name__ == '__main__':
    # Note: We will not run this file directly.
    # main.py will run the bot and this server in separate threads.
    socketio.run(app, debug=False)