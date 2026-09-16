
import streamlit as st
from db import get_db_connection
from nlp_sql_logic import (get_database_schema, normalize_query, 
                           normalize_fuzzy_logic, key_value_extraction, 
                           generate_sql, execute_sql)

import pandas as pd



st.set_page_config(
    page_title="Text2SQL",
    layout="centered"
)

st.title("Text2SQL")
st.caption("Natural language to SQL")



try:
    db = get_db_connection()
    connection_successful = True
    table_names, table_fields = get_database_schema(db)

except Exception as e:
    connection_successful = False
    db = None
    st.error(f"Database connection failed: {e}")


if connection_successful:

    st.success("Database connection established successfully!")

    st.markdown("### Database Schema")

    for i in range(0, len(table_names), 2):

        col1, col2 = st.columns(2)

        with col1:
            table = table_names[i]

            with st.expander(f"📋 {table}", expanded=False):
                for column in table_fields[table]:
                    st.markdown(f"• `{column}`")

        if i + 1 < len(table_names):

            with col2:
                table = table_names[i + 1]

                with st.expander(f"📋 {table}", expanded=False):
                    for column in table_fields[table]:
                        st.markdown(f"• `{column}`")



def submit_query():

    query = st.session_state.query_input

    if query.strip():

        query = normalize_query(query)

        query = normalize_fuzzy_logic(
            query,
            table_names
        )

        # Extract key-value information
        extracted_data = key_value_extraction(query)

        generated_sql = generate_sql(extracted_data)

        result = None

        if generated_sql:

            try:
                result = execute_sql(db, generated_sql)

            except Exception as e:
                result = {
                    "type": "ERROR",
                    "message": str(e)
                }

        st.session_state.submitted_query = query
        st.session_state.extracted_data = extracted_data
        st.session_state.generated_sql = generated_sql
        st.session_state.query_result = result
        st.session_state.query_input = ""

    else:

        st.session_state.submitted_query = None
        st.session_state.extracted_data = None
        st.session_state.generated_sql = None
        st.session_state.query_result = None

st.markdown("### Ask anything with your Text2SQL bot")

with st.form("query_form"):

    col1, col2 = st.columns([5, 1])

    with col1:
        st.text_input(
            "Your query",
            placeholder="e.g. Show employees older than 30...",
            label_visibility="collapsed",
            key="query_input"
        )

    with col2:
        st.form_submit_button(
            "Submit",
            use_container_width=True,
            on_click=submit_query
        )




st.write("Query Result:")

result = st.session_state.get("query_result")

if result:

    if result["type"] == "SELECT":

        df = pd.DataFrame(
            result["rows"],
            columns=result["columns"]
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    elif result["type"] == "ERROR":

        st.error(
            f"Query execution failed: {result['message']}"
        )