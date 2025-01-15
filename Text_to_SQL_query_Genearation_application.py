from dotenv import load_dotenv
load_dotenv()  # load all the environment variables

import streamlit as st
import os
import sqlite3
import csv
import io

import google.generativeai as genai

# Configure Genai Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Database file
# Connect to the SQLite database
db_file = os.path.join("C:\\Users\\mailt\\Desktop\\Capstone\\Gemini", "test.db")

def insert_csv_to_db(uploaded_file, table_name):
    # Connect to the database
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Check if the table already exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    table_exists = c.fetchone()

    if table_exists:
        st.error(f"Table '{table_name}' already exists. Data will not be inserted again.")
        conn.close()
        return

    # Create a StringIO object from the uploaded file
    csv_data = io.StringIO(uploaded_file.getvalue().decode("utf-8"))

    reader = csv.reader(csv_data)

    # Read the column names from the first row
    cols = next(reader)

    # Determine the data types for each column
    data_types = [None] * len(cols)  # Initialize with None
    for row in reader:
        if len(row) != len(cols):
            st.error(f"Error: Row length doesn't match the number of columns in the CSV file.")
            conn.close()
            return

        for i, value in enumerate(row):
            try:
                float(value)
                data_types[i] = "REAL"
            except ValueError:
                if value.isdigit():
                    data_types[i] = "INTEGER"
                else:
                    data_types[i] = "TEXT"
        break

    # Reset the reader
    csv_data.seek(0)
    reader = csv.reader(csv_data)
    next(reader)  # Skip the header row

    # Create dynamic column creation string
    column_defs = ','.join([f'{col} {data_types[i] or "TEXT"}' for i, col in enumerate(cols)])

    # Create the table
    c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})')

    # Insert the remaining rows
    for row in reader:
        if len(row) != len(cols):
            st.error(f"Error: Row length doesn't match the number of columns in the CSV file.")
            conn.rollback()
            break

        placeholders = ','.join('?' * len(row))
        sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        c.execute(sql, row)

    conn.commit()
    conn.close()
    st.success(f"Data inserted into '{table_name}' table successfully.")

def get_gemini_response(question, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt[0], question])
    return response.text

# Function To retrieve query from the database
def read_sql_query(sql, db_file, table_name):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        rows = []


    # Get the number of rows in the table
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    num_rows = cur.fetchone()[0]

    # Get the list of tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cur.fetchall()]

    # Get the column names
    cur.execute(f"PRAGMA table_info({table_name});")
    column_names = [row[1] for row in cur.fetchall()]

    conn.commit()
    conn.close()

    # Update the prompt with the table name and column names
    updated_prompt = [f"You are an expert in converting English questions to SQL query!\n\
        The SQL database has the table name '{table_name}' \
        with columns: {', '.join(column_names)}.\n\n\
        For example,\nExample 1 - How many entries of records are present?,\
          the SQL command will be something like this \
          SELECT COUNT(*) FROM table_name;. name the columns are in the table \
          SELECT name FROM pragma_table_info('table_name');\
          How many columns are in the table\
          SELECT COUNT(name) FROM pragma_table_info('table_name');\
            also the sql code should not have\
            ``` in beginning or end and sql word in output.\
            unerstand the column name and table name properly before giving SQL code."]

    return rows, updated_prompt,tables, num_rows

# Streamlit App
st.set_page_config(page_title="I can Retrieve Any SQL query from TEXT")
st.header("Gemini App To Retrieve SQL Data from TEXT")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv", help="Please upload the correct file")
if uploaded_file is not None:
    # Process the uploaded file
    file_details = {
        "filename": uploaded_file.name,
        "filetype": uploaded_file.type,
        "filesize": uploaded_file.size
    }
    st.write(file_details)
question = st.text_input("Input: ", key="input Question")
table_name = st.text_input("Table Name Input: ", key="input Table Name")
submit = st.button("Ask the question")

# if submit is clicked
if submit:
    if uploaded_file is not None:
        insert_csv_to_db(uploaded_file, table_name)

    response, updated_prompt, tables, num_rows = read_sql_query(question, db_file, table_name)
    st.write(f"Number of rows in '{table_name}' table: {num_rows}")
    st.write("Tables in the database:")
    for table in tables:
        st.write(f"- {table}")

    print(updated_prompt[0])
    response = get_gemini_response(question, updated_prompt)
    print(response)

    # Execute the SQL query and fetch the result
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(response)
    result = cur.fetchall()
    conn.commit()
    conn.close()

    st.subheader("The Response is")
    for row in result:
        st.write(row)