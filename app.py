# Russian translation and Render deployment ready
# Use this file to start the Flask webserver for Render
from webserver import app
import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8081)), debug=True)
