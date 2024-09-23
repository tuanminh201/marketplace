from flask import Flask
import secrets
import logging

app = Flask(__name__, template_folder="templates")  # relative path
app.config['SECRET_KEY'] = secrets.token_hex(16)
# Set up logging
logging.basicConfig(
    filename='app.log', 
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from routes import *


if __name__ == '__main__':
    app.run(debug=True)
 