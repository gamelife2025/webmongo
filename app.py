import streamlit as st
from pymongo import MongoClient
import pandas as pd

# Get query parameters
query_params = st.query_params
mongo_url = query_params.get('mongo_url', ['mongodb://localhost:27017/'])[0]
db_name = query_params.get('db', [None])[0]
collection_name = query_params.get('collection', [None])[0]

# MongoDB connection
client = MongoClient(mongo_url)

st.title("MongoDB Database Management Interface")

# Database selection
if db_name:
    db = client[db_name]
    st.write(f"Selected Database: {db_name}")
else:
    db_list = client.list_database_names()
    db_name = st.selectbox("Select Database", db_list)
    if db_name:
        db = client[db_name]
        st.query_params['db'] = db_name
    else:
        st.stop()

# Collection selection
if collection_name:
    collection = db[collection_name]
    st.write(f"Selected Collection: {collection_name}")
else:
    collection_list = db.list_collection_names()
    collection_name = st.selectbox("Select Collection", collection_list)
    if collection_name:
        collection = db[collection_name]
        st.query_params['collection'] = collection_name
    else:
        st.stop()

# Pagination controls
page_size_options = [10, 20, 50, 100]
page_size = st.selectbox("Items per page", page_size_options, index=0)

if 'page' not in st.session_state:
    st.session_state.page = 0

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("Previous Page") and st.session_state.page > 0:
        st.session_state.page -= 1
with col2:
    st.write(f"Page: {st.session_state.page + 1}")
with col3:
    if st.button("Next Page"):
        st.session_state.page += 1

# Query documents
skip = st.session_state.page * page_size
documents = list(collection.find().skip(skip).limit(page_size))

# Display documents
if documents:
    st.write(f"Showing {len(documents)} documents")
    for doc in documents:
        st.json(doc)
else:
    st.write("No documents found in this page.")