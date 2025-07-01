from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session  # Import Flask-Session
import pandas as pd
from data_processor import process_text, update_query  # Import function from separate file
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Keep this secure

# Configure server-side sessions
app.config['SESSION_TYPE'] = 'filesystem'  # Options: 'redis', 'sqlalchemy', 'memcached', etc.
app.config['SESSION_FILE_DIR'] = './.flask_session/'  # Optional: directory for session files
app.config['SESSION_PERMANENT'] = False  # Optional: False = expire on browser close
Session(app)  # Initialize session backend

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    text_input = request.form.get('text_input')
    if text_input:
        # Call function from separate Python file
        csv_data,sparql_text = process_text(text_input)

        # Store CSV data in session for display (now server-side)
        session['csv_data'] = csv_data
        session['sparql_text']=sparql_text
        
        return redirect(url_for('results'))
    return redirect(url_for('index'))

@app.route('/results')
def results():
    csv_data = session.get('csv_data', [])
    sparql_text = session.get('sparql_text',"no query created")
    return render_template('results.html', csv_data=csv_data,sparql_text=sparql_text)

@app.route('/execute-query', methods=['POST'])
def execute_query():
    data = request.get_json()
    sparql_query = data.get('query', '')

    updated_data,updated_query=update_query(sparql_query)

    return render_template('results.html', csv_data=updated_data,sparql_text=updated_query)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

