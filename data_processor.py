import csv
import openai
from SPARQLWrapper import SPARQLWrapper, CSV, SPARQLExceptions
import time
import sample_finder
from dotenv import load_dotenv
import os


#loads .env file
load_dotenv()
   
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

def get_query(props,question):
    """
    This retrieves the query for the knowledge graph
    Args:
        props (string): a list of used classes and properties
        question (string): chatgpt prompt question
    Returns:
        str: chatgpt response (returns only the contructed query)
    """
    #pulls a string of sample knowledge graph entry from sample_finder.py
    sample=sample_finder.get_sample(props)
    #pulls prompt template
    template = load_template('prompt.txt')
    #populates sample and props information into system
    system = eval(f'f"""{template}"""')
    return remove_first_and_last_line(gpt_call(system,question))
    
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
    
def get_used_prop(question):
    """
    This function retrives the field_prompt to prompt chatgpt
    Args:
        question (string): the question asked by the user
    Returns:
        str: lists important properties and classes in this structure - class1[property1,property2,property3]class2[property1,property2,property3]
    """
    template = load_template('field_prompt.txt')  # Reads the above string

    message = eval(f'f"""{template}"""')  # Evaluates as f-string
    print(message)

def process_text(question):
    """
    This calls all needed functions for the full graphRAG pipeline
    Args:
        question (string): the question asked by the user
    Returns:
        list: converted csv file holding the query output
    """
    if question == "test":
        with open('test.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)
        return data,"this is a test"
    props=gpt_call(load_template('field_prompt.txt'),question)
    print("field prompt is: ", props,"\n------------------")
    query=get_query(props,question)
    print("query is: \n", query,"\n------------------")
    query_database(query)
    with open('query-result.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
    return data,query

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