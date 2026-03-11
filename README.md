# MongoDB Management Interface

A simple web interface for managing MongoDB databases using Streamlit.

## Features

- Select database and collection via URL parameters or UI
- Paginated view of documents
- Configurable page size

## Requirements

- Python 3.7+
- MongoDB running locally on port 27017
- Required packages: streamlit, pymongo

## Installation

1. Clone or download the project
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure MongoDB is running

## Usage

Run the application:
```
streamlit run app.py
```

Access the interface at http://localhost:8501

### URL Parameters

- `mongo_url`: MongoDB connection URL (default: mongodb://localhost:27017/)
- `db`: Database name
- `collection`: Collection name

Example: http://localhost:8501/?mongo_url=mongodb://localhost:27017/&db=mydatabase&collection=mycollection

## Notes

- Assumes MongoDB is running locally on default port
- For large datasets, use pagination controls