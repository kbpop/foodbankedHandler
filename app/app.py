from flask import Flask

# Initialize the Flask application instance
app = Flask(__name__)

# Define the root URL route and its behavior
@app.route("/")
def home():
    return "<h1>Hello, World!</h1><p>My new Flask app is running.</p>"

# Run the local development server with debugging enabled
if __name__ == "__main__":
    app.run(debug=True)