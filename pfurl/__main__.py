from flask import Flask, render_template
from hashids import Hashids
import random
from short import generate_hash

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('base.html')

if __name__ == "__main__":
    app.run()