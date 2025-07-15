# -----------------------------------------------------------------------------
#
# This is the main file for my flask gui code to run my GraphRAG Pipeline
#
# -----------------------------------------------------------------------------
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session  
import pandas as pd
from pipeline_runner import pull_pipeline, update_query  

#set up app
app = Flask(__name__)

#app configuration
app.config['SESSION_TYPE'] = 'filesystem' 
app.config['SESSION_FILE_DIR'] = './.flask_session/'  
app.config['SESSION_PERMANENT'] = False  
Session(app)

#opens index.html
@app.route('/')
def index():
    return render_template('index.html')

#processes question when enter button is hit
@app.route('/process', methods=['POST'])
def process():
    text_input = request.form.get("text_input","")
    if not text_input or "invalid" in text_input:
        return render_template("index.html",error="Invalid input, ask a question related to MIMIC FHIR")
    if text_input:
        # Call function from separate Python file
        csv_data,sparql_text = pull_pipeline(text_input)
        if sparql_text=="invalid":
            return render_template("index.html",error="Invalid input, ask a question related to MIMIC FHIR")
        # Store CSV data in session for display
        session['csv_data'] = csv_data
        session['sparql_text']=sparql_text
        
        return redirect(url_for('results'))
    return redirect(url_for('index'))

#gets returned results from process and outputs them in results.html
@app.route('/results')
def results():
    csv_data = session.get('csv_data', [])
    sparql_text = session.get('sparql_text',"no query created")
    return render_template('results.html', csv_data=csv_data,sparql_text=sparql_text)

#executes query again if you edit the query in the results.html page
@app.route('/execute-query', methods=['POST'])
def execute_query():
    data = request.get_json()
    sparql_query = data.get('query', '')

    updated_data,updated_query=update_query(sparql_query)

    return render_template('results.html', csv_data=updated_data,sparql_text=updated_query)

#runs flask server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)



