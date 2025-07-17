#imports
import csv
import openai
from SPARQLWrapper import SPARQLWrapper, CSV, SPARQLExceptions, JSON
import time
from dotenv import load_dotenv
import os
import json

#loads env file holding sensitive information like api keys and passwords
load_dotenv()


#--------------------
#
# Note first_prompt.txt holds the first prompt to pass through the LLM to select the template
#
# Templates are held in the query_templates folder (templates folder holds html files for the gui)
#
#--------------------
   
def gpt_call(system,prompt):
    """
    This fuction calls gpt-4o and returns the answer
    Args:
        system (string): instructions for the LLM before the query
        prompt (string): chatgpt prompt
    Returns:
        str: chatgpt response
    """
    client = openai.OpenAI(api_key=os.getenv("gpt_api_key"))
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ],
        max_tokens=16384,
    )
    return response.choices[0].message.content

def load_template(filename):
    """
    This fuction opens a file and reads it
    Args:
        filename (string): path to the file name *if not in folder have to put the full path* 
    Returns:
        str: everything inside of the file
    """
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

def remove_first_and_last_line(text):
    """
    This removes the first and last line of a piece of text(used because chatgpt output have ``` brackets around them)
    Args:
        text (string): a piece of text
    Returns:
        str: chatgpt response (returns only the contructed query)
    """
    lines = text.splitlines()
    if len(lines) <= 2:
        return ""  # Nothing to return if there's only 1 or 2 lines
    return "\n".join(lines[1:-1])

def query_database(query):
    """
    This function queries the knowledge graph database (graphDB) and writes the output to query-result.csv
    Args:
        query (string): a sparql query for the database
    Returns:
        None : writes output to query-result.csv
    """
    sparql = SPARQLWrapper(os.getenv("graphdb_repo"))
    sparql.setCredentials(os.getenv("graphdb_username"), os.getenv("graphdb_password"))
    sparql.setReturnFormat(CSV)
    try:
        sparql.setQuery(query)
        response = sparql.query()
        csv_results = response.convert().decode("utf-8")
        with open("query-result.csv", "w", encoding="utf-8") as f:
            f.write(csv_results)
    except SPARQLExceptions.QueryBadFormed as e:
        print("SPARQL query is malformed:", e)
        with open("query-result.csv", "w", encoding="utf-8") as f:
            f.write("Error: Failed to execute SPARQL query\n")
    except Exception as e:
        print("An unexpected error occurred:", e)
        with open("query-result.csv", "w", encoding="utf-8") as f:
            f.write("Error: Failed to execute SPARQL query\n")

def pull_pipeline(question):
    """
    This function contains the full GraphRAG pipeline
    Args:
        question (string): nl question given from user input in the gui
    Returns:
        data : csv ouput from querying the database
        sparql_query : string holding the sparql query that was passed through the database
    """
    first_prompt=gpt_call(load_template('first_prompt.txt'),question)
    print("template selected is: ",first_prompt)
    sparql_query=""
    if first_prompt=="Condition query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_condition.txt'),question))
    elif first_prompt=="Specimen query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_specimen.txt'),question))
    elif first_prompt=="Encounter query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_encounter.txt'),question))
    elif first_prompt=="Location query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_location.txt'),question))
    elif first_prompt=="Organization query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_organization.txt'),question))
    elif first_prompt=="Procedure query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_procedure.txt'),question))
    elif first_prompt=="MedicationAdministration query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_medicationAdministration.txt'),question))
    elif first_prompt=="Observation query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_observation.txt'),question))
    elif first_prompt=="Medication query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_medication.txt'),question))
    elif first_prompt=="MedicationDispense query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_medicationDispense.txt'),question))
    elif first_prompt=="Patient query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient.txt'),question))
    elif first_prompt=="MedicationRequest query":
        sparql_query=remove_first_and_last_line(gpt_call(load_template('query_templates/patient_medicationRequest.txt'),question))
    elif first_prompt=="none of the above":
        print("none of the above error")
        return [],"invalid"
    else:
        print("error with first prompt")
        return [],"invalid"
    print("querying database")
    query_database(sparql_query)
    print("database queried")
    with open('query-result.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
    return data,sparql_query

def update_query(query):
    """
    This updates the page if the user edits the query in the gui
    Args:
        query (string): user updated query
    Returns:
        list: converted csv file holding the query output
    """
    query_database(query)
    with open('query-result.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
    return data,query

