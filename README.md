# NLP-to-SQL Pipeline

An NLP-to-SQL system that converts natural-language database queries into executable SQL. The project is built from scratch to explore how natural-language understanding, schema awareness, and semantic matching can be combined to make relational databases easier to interact with.

## Overview

Instead of writing SQL manually, users can enter queries such as:

> "Show the names and salaries of employees older than 30"

The system processes the request, identifies the user's intent, relevant table, columns, and conditions, generates the corresponding SQL query, and executes it against a MySQL database.

### Current Pipeline

```text
Natural Language Query
        ↓
Query Normalization
        ↓
Intent & Entity Extraction
        ↓
Schema-Aware SQL Generation
        ↓
SQL Query Execution
        ↓
Database Results
```

## Features

* Natural-language querying of MySQL databases
* Automatic intent extraction
* Table and column identification
* Condition extraction with operators such as:

  * `=`
  * `>`
  * `<`
  * `>=`
  * `<=`
* Dynamic SQL generation
* MySQL database execution
* Streamlit-based interface
* Database schema inspection
* Fuzzy matching experiments for handling misspelled table names
* Gemini API integration for structured natural-language extraction

## Example

### Input

```text
Show the names and salaries of employees older than 30
```

### Generated SQL

```sql
SELECT name, salary
FROM employees
WHERE age > 30;
```

The query is then executed against the connected MySQL database and the resulting records are displayed in the Streamlit interface.

## Tech Stack

* **Python**
* **MySQL**
* **Streamlit**
* **Google Gemini API**
* **spaCy**
* **RapidFuzz**
* **Pandas**
* **python-dotenv**

## Project Structure

```text
NLP-to-SQL/
│
├── app.py                 # Streamlit frontend
├── db.py                  # MySQL database connection
├── nlp_sql_logic.py       # NLP processing and SQL generation
├── .env                   # API credentials (not committed)
├── .gitignore
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd NLP-to-SQL
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
```

Do **not** commit your `.env` file to GitHub.

Add it to `.gitignore`:

```text
.env
__pycache__/
```

### 4. Configure MySQL

Make sure MySQL is running and update the database connection settings in `db.py` according to your local database.

### 5. Run the application

```bash
streamlit run app.py
```

The application will open locally in your browser.

## Current Scope

The current implementation focuses on **SELECT queries** and basic filtering.

Supported examples include:

```text
Show all employees

Show employee names

Show employee names and salaries

Show employees older than 30

Show employees with salary greater than 50000

Show employees in the IT department

Show sales with amount greater than 10000
```

More advanced capabilities such as aggregation, sorting, joins, and modification queries are planned for future development.

## Future Improvements

* `MAX`, `MIN`, `AVG`, `SUM`, and `COUNT`
* `ORDER BY`
* `GROUP BY`
* SQL joins
* More robust schema-aware semantic matching
* Better handling of ambiguous natural-language queries
* Query validation before execution
* Support for additional SQL operations
* Improved error handling and query explanation
* More extensive evaluation using a natural-language/SQL test dataset

## Goal

The goal of this project is to understand and build the core components of a natural-language database interface rather than relying entirely on an end-to-end text-to-SQL framework.
