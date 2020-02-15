from flask import flash, Flask, render_template, request
from forms import QueryForm
from flask_wtf.csrf import CSRFProtect
import os, sys, houndify
import speech_recognition as sr
from phrase_occurrences import find_occurrences

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)
csrf = CSRFProtect(app)

SECRET_KEY = 'go bears'
app.config['SECRET_KEY'] = SECRET_KEY
client_id = app.config['HOUNDIFY_ID']
client_key = app.config['HOUNDIFY_KEY']
user_id = app.config['HOUNDIFY_USR']
client = houndify.StreamingHoundClient(client_id, client_key, user_id, sampleRate=8000)

@app.route('/', methods=('GET', 'POST'))
def home():
    search = QueryForm(request.form)
    if request.method == 'POST':
        search_string = request.form['query']
        data = find_occurrences(search_string, "examples/andrew_ng/andrew_ng.json")
        return render_template('index.html', form=search, name=search_string, data=data)
    return render_template('index.html', form=search)

@app.route("/listen", methods=['POST'])
def listen():
    search = QueryForm(request.form)
    if request.method == 'POST':
        rec = sr.Recognizer()
        with sr.Microphone() as source:
            rec.adjust_for_ambient_noise(source)
            app.logger.info("I'm listening...")
            audio = rec.listen(source, phrase_time_limit=5)
        search_string = rec.recognize_houndify(audio, client_id, client_key)
        if search_string:
            data = find_occurrences(search_string, "examples/andrew_ng/andrew_ng.json")
            return render_template('index.html', form=search, name=search_string, data=data)
    return render_template('index.html', form=search)

if __name__ == "__main__":
    app.run(debug=True)