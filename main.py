from flask import flash, Flask, render_template, request
from forms import QueryForm
from flask_wtf.csrf import CSRFProtect
import os
import sys
from phrase_occurances import find_occurances

app = Flask(__name__)
app.config.from_object(__name__)
csrf = CSRFProtect(app)

SECRET_KEY = 'go bears'
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/', methods=('GET', 'POST'))
def home():
    search = QueryForm(request.form)
    if request.method == 'POST':
        search_string = request.form['query']
        data = find_occurances(search_string, "examples/andrew_ng/andrew_ng.json")
        return render_template('index.html', form=search, name=search_string, data=data)
    return render_template('index.html', form=search)

if __name__ == "__main__":
    app.run(debug=True)