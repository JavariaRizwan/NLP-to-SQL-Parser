import re
from rapidfuzz import process, fuzz
import os
from dotenv import load_dotenv
from google import genai
import json


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# get all the tables and their columns from the database
def get_database_schema(db):

    cursor = db.cursor()

    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    table_names = []
    table_fields = {}

    for table in tables:

        table_name = table[0]

        table_names.append(table_name)

        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()

        table_fields[table_name] = [
            column[0] for column in columns
        ]

    cursor.close()

    return table_names, table_fields


def normalize_query(user_query):

    query = user_query.lower()
    query = re.sub(r"\s+", " ", query).strip()

    query = re.sub(r"[^\w\s><=]", "", query)

    return query



def normalize_fuzzy_logic(user_query, table_names):

    words = user_query.lower().split()

    normalized_words = []

    for word in words:

        match = process.extractOne(
            word,
            table_names,
            scorer=fuzz.ratio
        )

        if match:
            matched_table, score, _ = match

            if score >= 70:
                normalized_words.append(matched_table)
            else:
                normalized_words.append(word)

        else:
            normalized_words.append(word)

    return " ".join(normalized_words)


def key_value_extraction(user_query):

    prompt = f"""
You are an NLP-to-SQL query understanding system.

Your job is to understand a user's natural language database query
and extract its structured meaning.

IMPORTANT RULES:

1. DO NOT generate SQL.
2. DO NOT explain your answer.
3. Return ONLY valid JSON.
4. DO NOT invent table names or column names.
5. Extract only information expressed or clearly implied by the user.
6. Preserve numeric values as numbers when appropriate.
7. Preserve text values as strings.
8. Correct obvious spelling mistakes when the intended database
   table or column is clear from context.

Return ONLY JSON using exactly this structure:

{{
    "intent": "SELECT | UPDATE | DELETE | CREATE",
    "table": "table_name",
    "select_columns": ["column_name"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "column_name",
            "operator": "= | > | < | >= | <=",
            "value": "value"
        }}
    ]
}}

FIELD DEFINITIONS:

- intent:
  The database operation requested by the user.

- table:
  The database table involved in the request.

- select_columns:
  The columns the user wants returned for SELECT queries.
  
  If the user does not specify particular columns and asks for
  records, employees, sales, vendors, etc., use ["*"].

  If the user asks for specific columns, return those columns.

  Examples:
  "show employees" -> ["*"]
  "show employee names" -> ["name"]
  "show names and salaries" -> ["name", "salary"]

- target_column:
  Used only for UPDATE.
  
  It is the column whose value should be changed.

  For SELECT, DELETE and CREATE, use null.

- target_value:
  Used only for UPDATE.
  
  It is the new value that should be assigned to target_column.

  For SELECT, DELETE and CREATE, use null.

- conditions:
  Conditions that determine which database records are affected
  or returned.

  Each condition contains:
  - column
  - operator
  - value

SELECT RULES:

- select_columns contains the requested output columns.
- If no specific output column is mentioned, use ["*"].
- target_column must be null.
- target_value must be null.
- conditions contain filtering conditions.

UPDATE RULES:

- select_columns must be ["*"].
- target_column is the column being changed.
- target_value is the new value.
- conditions determine which records are updated.

DELETE RULES:

- select_columns must be ["*"].
- target_column must be null.
- target_value must be null.
- conditions determine which records are deleted.

CREATE RULES:

- select_columns must be [].
- Extract the intended table name.
- target_column must be null.
- target_value must be null.
- conditions must be [].

EXAMPLES:

1. SELECT ALL COLUMNS

User:
"Show me employees older than 30"

Extract:
{{
    "intent": "SELECT",
    "table": "employees",
    "select_columns": ["*"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "age",
            "operator": ">",
            "value": 30
        }}
    ]
}}


2. SELECT SPECIFIC COLUMN

User:
"Show the names of employees whose salary is greater than 50"

Extract:
{{
    "intent": "SELECT",
    "table": "employees",
    "select_columns": ["name"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "salary",
            "operator": ">",
            "value": 50
        }}
    ]
}}


3. SELECT MULTIPLE COLUMNS

User:
"Show the names and salaries of employees older than 30"

Extract:
{{
    "intent": "SELECT",
    "table": "employees",
    "select_columns": ["name", "salary"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "age",
            "operator": ">",
            "value": 30
        }}
    ]
}}


4. SELECT WITH EQUALITY

User:
"Find employees in the IT department"

Extract:
{{
    "intent": "SELECT",
    "table": "employees",
    "select_columns": ["*"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "department",
            "operator": "=",
            "value": "IT"
        }}
    ]
}}


5. UPDATE

User:
"Change the salary of employees older than 30 to 60000"

Extract:
{{
    "intent": "UPDATE",
    "table": "employees",
    "select_columns": ["*"],
    "target_column": "salary",
    "target_value": 60000,
    "conditions": [
        {{
            "column": "age",
            "operator": ">",
            "value": 30
        }}
    ]
}}


6. UPDATE

User:
"Set the discount to 20 for sales worth more than 10000"

Extract:
{{
    "intent": "UPDATE",
    "table": "sales",
    "select_columns": ["*"],
    "target_column": "discount",
    "target_value": 20,
    "conditions": [
        {{
            "column": "amount",
            "operator": ">",
            "value": 10000
        }}
    ]
}}


7. DELETE

User:
"Delete employees whose age is below 25"

Extract:
{{
    "intent": "DELETE",
    "table": "employees",
    "select_columns": ["*"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "age",
            "operator": "<",
            "value": 25
        }}
    ]
}}


8. DELETE

User:
"Remove vendors with a rating less than 3"

Extract:
{{
    "intent": "DELETE",
    "table": "vendors",
    "select_columns": ["*"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "rating",
            "operator": "<",
            "value": 3
        }}
    ]
}}


9. CREATE

User:
"Create a new table called customers"

Extract:
{{
    "intent": "CREATE",
    "table": "customers",
    "select_columns": [],
    "target_column": null,
    "target_value": null,
    "conditions": []
}}


10. SELECT WITHOUT CONDITION

User:
"Show all employees"

Extract:
{{
    "intent": "SELECT",
    "table": "employees",
    "select_columns": ["*"],
    "target_column": null,
    "target_value": null,
    "conditions": []
}}


11. SELECT SPECIFIC COLUMNS WITHOUT CONDITION

User:
"Give me the names and departments of all employees"

Extract:
{{
    "intent": "SELECT",
    "table": "employees",
    "select_columns": ["name", "department"],
    "target_column": null,
    "target_value": null,
    "conditions": []
}}


12. SELECT WITH MULTIPLE CONDITIONS

User:
"Show the names of employees older than 30 with salary greater than 50000"

Extract:
{{
    "intent": "SELECT",
    "table": "employees",
    "select_columns": ["name"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "age",
            "operator": ">",
            "value": 30
        }},
        {{
            "column": "salary",
            "operator": ">",
            "value": 50000
        }}
    ]
}}


13. UPDATE WITH EQUALITY CONDITION

User:
"Set the salary to 70000 for employees in the IT department"

Extract:
{{
    "intent": "UPDATE",
    "table": "employees",
    "select_columns": ["*"],
    "target_column": "salary",
    "target_value": 70000,
    "conditions": [
        {{
            "column": "department",
            "operator": "=",
            "value": "IT"
        }}
    ]
}}


14. DELETE WITH CONDITION

User:
"Delete vendors whose rating is less than 3"

Extract:
{{
    "intent": "DELETE",
    "table": "vendors",
    "select_columns": ["*"],
    "target_column": null,
    "target_value": null,
    "conditions": [
        {{
            "column": "rating",
            "operator": "<",
            "value": 3
        }}
    ]
}}


Now extract the information from this user query.

User:
{user_query}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return json.loads(response.text)


def generate_sql(parsed_query):

    intent = parsed_query["intent"]
    table = parsed_query["table"]
    select_columns = parsed_query["select_columns"]
    target_column = parsed_query["target_column"]
    target_value = parsed_query["target_value"]
    conditions = parsed_query["conditions"]

    # Build WHERE clause
    where_parts = []

    for condition in conditions:
        column = condition["column"]
        operator = condition["operator"]
        value = condition["value"]

        if isinstance(value, str):
            value = f"'{value}'"

        where_parts.append(
            f"{column} {operator} {value}"
        )

    where_clause = ""

    if where_parts:
        where_clause = " WHERE " + " AND ".join(where_parts)

    # SELECT
    if intent == "SELECT":

        columns = ", ".join(select_columns)

        return f"SELECT {columns} FROM {table}{where_clause};"

    # UPDATE
    elif intent == "UPDATE":

        if not conditions:
            return None

        if isinstance(target_value, str):
            target_value = f"'{target_value}'"

        return (
            f"UPDATE {table} "
            f"SET {target_column} = {target_value}"
            f"{where_clause};"
        )

    # DELETE
    elif intent == "DELETE":

        if not conditions:
            return None

        return f"DELETE FROM {table}{where_clause};"

    # CREATE
    elif intent == "CREATE":

        return None

    return None    



def execute_sql(db, generated_sql):

    cursor = db.cursor()

    try:

        cursor.execute(generated_sql)

        rows = cursor.fetchall()

        columns = [
            description[0]
            for description in cursor.description
        ]

        return {
            "type": "SELECT",
            "columns": columns,
            "rows": rows
        }

    finally:

        cursor.close()