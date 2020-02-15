from flask import flash, Flask, render_template, request
from forms import QueryForm
from flask_wtf.csrf import CSRFProtect
import os
import sys

app = Flask(__name__)
app.config.from_object(__name__)
csrf = CSRFProtect(app)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/', methods=('GET', 'POST'))
def home():
    search = QueryForm(request.form)
    if request.method == 'POST':
        search_string = request.form['query']
        return render_template('index.html', form=search, name=search_string)
    return render_template('index.html', form=search)

if __name__ == "__main__":
    app.run(debug=True)