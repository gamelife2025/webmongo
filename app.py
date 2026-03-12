import json
import os
import uuid

import pandas as pd
import streamlit as st
from bson import ObjectId
from pymongo import MongoClient

# --- 1. Constants & Configuration ---
CONN_FILE = "connections.json"
TABS_FILE = "last_tabs.json"

st.set_page_config(page_title="Streamlit Compass", page_icon="🧭", layout="wide")

# --- 2. Custom CSS for Beautiful UI ---
def load_css():
    st.markdown(
        """
        <style>
        /* Main background and font */
        .stApp {
            background-color: #f4f7f6;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 98%;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #001e2b;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            border-bottom: 2px solid #e8edea;
            padding-bottom: 0;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0px 0px;
            padding: 12px 24px;
            background-color: #ffffff;
            border: 1px solid #e8edea;
            border-bottom: none;
            color: #5c6c75;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.02);
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #00684a;
            background-color: #f9fbfb;
            border-color: #c1c7c6;
        }
        .stTabs [aria-selected="true"] {
            background-color: #e3fcfa;
            border-bottom: 3px solid #00ed64;
            color: #001e2b;
            font-weight: 700;
        }
        
        /* Buttons */
        .stButton button {
            border-radius: 6px;
            font-weight: 600;
            border: 1px solid #c1c7c6;
            transition: all 0.2s;
            height: 42px;
        }
        .stButton button:hover {
            border-color: #00ed64;
            color: #00684a;
            box-shadow: 0 2px 4px rgba(0,237,100,0.1);
        }
        .stButton button[kind="primary"] {
            background-color: #00684a;
            color: white;
            border: none;
        }
        .stButton button[kind="primary"]:hover {
            background-color: #00ed64;
            color: #001e2b;
            box-shadow: 0 4px 8px rgba(0,237,100,0.3);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e8edea;
        }
        .sidebar-title {
            color: #001e2b;
            font-size: 26px;
            font-weight: 800;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #001e2b;
            background-color: #f9fbfb;
            border-radius: 6px;
        }
        .streamlit-expanderContent {
            border: 1px solid #e8edea;
            border-top: none;
            border-radius: 0 0 6px 6px;
        }
        
        /* Data table container */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            overflow: hidden;
            border: 1px solid #e8edea;
        }
        
        /* Input fields and Selectboxes */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            border-radius: 6px;
            border: 1px solid #c1c7c6;
            height: 42px;
        }
        .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
            border-color: #00ed64;
            box-shadow: 0 0 0 2px rgba(0,237,100,0.2) !important;
        }

        /* Radio Buttons */
        div[role="radiogroup"] {
            padding: 4px 8px;
            background-color: #ffffff;
            border: 1px solid #e8edea;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# --- 3. Data Loading & Saving ---
def load_json(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default_val
    return default_val

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_connections():
    return load_json(CONN_FILE, {"Localhost": "mongodb://localhost:27017/"})

def load_tabs():
    return load_json(TABS_FILE, [])

def save_state():
    save_json(CONN_FILE, st.session_state.connections)
    save_json(TABS_FILE, st.session_state.open_tabs)

# --- 4. Session State Initialization ---
def init_session_state():
    if "connections" not in st.session_state:
        st.session_state.connections = load_connections()
    if "open_tabs" not in st.session_state:
        st.session_state.open_tabs = load_tabs()
    if "queries" not in st.session_state:
        st.session_state.queries = {}

# --- 5. MongoDB Operations ---
@st.cache_resource(ttl=3600)
def get_mongo_client(uri: str):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        return client
    except Exception as e:
        # Avoid caching failed connections by catching where we call this and handling there too
        return None

def serialize_bson(document: dict) -> dict:
    for key, value in document.items():
        if isinstance(value, ObjectId):
            document[key] = str(value)
    return document

# --- 6. UI Components ---
def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-title"><span style="color:#00ed64">🧭</span> WebMongo</div>',
            unsafe_allow_html=True,
        )

        with st.expander("➕ Add New Connection", expanded=False):
            new_conn_name = st.text_input("Connection Name", placeholder="e.g., Prod DB")
            new_conn_uri = st.text_input("MongoDB URI", placeholder="mongodb://localhost:27017/")
            if st.button("Save Connection", use_container_width=True, type="primary"):
                if new_conn_name and new_conn_uri:
                    st.session_state.connections[new_conn_name] = new_conn_uri
                    save_state()
                    st.rerun()

        st.divider()
        st.markdown(
            f"<div style='color:#5c6c75; font-weight:700; font-size: 0.85em; margin-bottom: 12px; letter-spacing: 0.5px;'>SAVED CONNECTIONS ({len(st.session_state.connections)})</div>",
            unsafe_allow_html=True,
        )

        for conn_name, conn_uri in list(st.session_state.connections.items()):
            # Determine if this connection should be expanded based on the last active tab
            expanded = False
            selected_db_default = None
            selected_coll_default = None
            
            if st.session_state.open_tabs:
                last_tab = st.session_state.open_tabs[-1]
                if last_tab["conn_name"] == conn_name:
                    expanded = True
                    selected_db_default = last_tab["db"]
                    selected_coll_default = last_tab["coll"]
            
            with st.expander(f"🔌 {conn_name}", expanded=expanded):
                client = get_mongo_client(conn_uri)
                if client is None:
                    st.error("Connection failed")
                    if st.button("Remove Connection", key=f"rm_{conn_name}", use_container_width=True):
                        del st.session_state.connections[conn_name]
                        save_state()
                        st.rerun()
                    continue

                try:
                    db_names = [
                        db for db in client.list_database_names()
                        if db not in ["admin", "config", "local"]
                    ]
                    
                    if not db_names:
                        st.info("No available databases.")
                        continue

                    # Select Database
                    db_index = db_names.index(selected_db_default) if selected_db_default in db_names else 0
                    selected_db = st.selectbox(
                        "Database",
                        db_names,
                        key=f"db_{conn_name}",
                        index=db_index,
                        label_visibility="collapsed"
                    )

                    if selected_db:
                        # Select Collection
                        collections = client[selected_db].list_collection_names()
                        if not collections:
                            st.info("No collections found.")
                        else:
                            coll_index = collections.index(selected_coll_default) if selected_coll_default in collections else 0
                            selected_coll = st.selectbox(
                                "Collection",
                                sorted(collections),
                                key=f"coll_{conn_name}_{selected_db}",
                                index=coll_index,
                                label_visibility="collapsed"
                            )

                            if selected_coll:
                                if st.button("Open Tab", key=f"btn_{conn_name}_{selected_db}_{selected_coll}", use_container_width=True):
                                    # Ensure no duplicate exact tab is opened
                                    tab_id = str(uuid.uuid4())[:8]
                                    st.session_state.open_tabs.append({
                                        "id": tab_id,
                                        "conn_name": conn_name,
                                        "conn_uri": conn_uri,
                                        "db": selected_db,
                                        "coll": selected_coll,
                                    })
                                    st.session_state.queries[tab_id] = "{}"
                                    save_state()
                                    st.rerun()

                except Exception as e:
                    st.error(f"Permissions/Read error: {e}")

def render_empty_state():
    st.write("<br>" * 5, unsafe_allow_html=True)
    st.markdown(
        """
        <div style='text-align:center; padding: 60px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); max-width: 600px; margin: 0 auto; border: 1px solid #e8edea;'>
            <div style="font-size: 64px; margin-bottom: 20px;">🍃</div>
            <h2 style='color:#001e2b; margin-bottom: 15px; font-weight: 800;'>Welcome to WebMongo</h2>
            <p style='color:#5c6c75; font-size: 1.15em; line-height: 1.6;'>
                Select a database and collection from the sidebar<br>to start exploring your MongoDB data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_tab_content(tab_data, idx):
    t_id = tab_data["id"]
    conn_uri = tab_data["conn_uri"]
    db_name = tab_data["db"]
    coll_name = tab_data["coll"]

    # Header section with breadcrumbs and close button
    header_col1, header_col2 = st.columns([12, 1])
    with header_col1:
        st.markdown(
            f"""
            <div style='background-color: #ffffff; padding: 14px 20px; border-radius: 8px; border: 1px solid #e8edea; margin-bottom: 20px; display: flex; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.02);'>
                <span style='color: #889397; margin-right: 12px; font-weight: 500;'>🔌 {tab_data['conn_name']}</span>
                <span style='color: #d1d7d6; margin-right: 12px;'>/</span>
                <span style='color: #001e2b; font-weight: 600; margin-right: 12px;'>📁 {db_name}</span>
                <span style='color: #d1d7d6; margin-right: 12px;'>/</span>
                <span style='color: #00684a; font-weight: 800;'>📄 {coll_name}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with header_col2:
        if st.button("✖", key=f"close_{t_id}", help="Close tab", use_container_width=True):
            st.session_state.open_tabs.pop(idx)
            st.session_state.queries.pop(t_id, None)
            save_state()
            st.rerun()

    # Query Bar Setup
    query_container = st.container()
    
    # We create the layout columns
    q_col1, q_col2, q_col3, q_col4 = query_container.columns([5, 2, 2, 2])
    
    with q_col1:
        query_str = st.text_input(
            "Filter Query",
            value=st.session_state.queries.get(t_id, "{}"),
            key=f"q_{t_id}",
            label_visibility="collapsed",
            placeholder='{ "field": "value" }',
        )
        
    with q_col2:
        limit_val = st.selectbox(
            "Limit",
            options=[50, 100, 200, 500],
            index=0,
            key=f"l_{t_id}",
            label_visibility="collapsed",
        )
        
    with q_col4:
        st.button("🔍 Find Query", key=f"f_{t_id}", type="primary", use_container_width=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # Validate and Parse Query
    try:
        query_dict = json.loads(query_str or "{}")
        st.session_state.queries[t_id] = query_str
    except json.JSONDecodeError:
        st.error("⚠️ Invalid JSON format in filter query. Keys must be enclosed in double quotes.")
        return

    # Database Connection
    client = get_mongo_client(conn_uri)
    if not client:
        st.error("Failed to connect to database.")
        return
        
    collection = client[db_name][coll_name]
    
    try:
        total_count = collection.count_documents(query_dict)
    except Exception as e:
        st.error(f"❌ Query execution error: {e}")
        return

    if total_count == 0:
        st.info("No documents found matching the filter criteria.")
        return

    # Pagination logic
    max_page = max(1, (total_count + limit_val - 1) // limit_val)
    page_key = f"page_{t_id}"
    
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
        
    # Reset page safely if bounds change
    if st.session_state[page_key] > max_page:
        st.session_state[page_key] = 1

    current_page = st.session_state[page_key]
    
    # Render Pagination in the prepared column slot
    with q_col3:
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if st.button("◀", key=f"prev_{t_id}", disabled=(current_page <= 1), use_container_width=True):
                st.session_state[page_key] -= 1
                st.rerun()
        with p_col2:
            st.markdown(f"<div style='text-align:center; padding-top: 10px; font-weight: 700; color: #001e2b;'>{current_page} / {max_page}</div>", unsafe_allow_html=True)
        with p_col3:
            if st.button("▶", key=f"next_{t_id}", disabled=(current_page >= max_page), use_container_width=True):
                st.session_state[page_key] += 1
                st.rerun()

    # Query Execution
    skip_val = (current_page - 1) * limit_val
    try:
        cursor = collection.find(query_dict).skip(skip_val).limit(limit_val)
        docs = [serialize_bson(doc) for doc in cursor]
        
        start_idx = skip_val + 1
        end_idx = skip_val + len(docs)
        
        # Results Header
        res_col1, res_col2 = st.columns([8, 2])
        with res_col1:
            st.markdown(f"<div style='color:#5c6c75; font-size: 0.95em; padding-top: 10px; font-weight: 500;'>Showing <span style='color:#001e2b;font-weight:700;'>{start_idx} - {end_idx}</span> of <span style='color:#001e2b;font-weight:700;'>{total_count}</span> documents</div>", unsafe_allow_html=True)
        with res_col2:
            view_mode = st.radio(
                "View Mode",
                ["Table Layout", "JSON Format"],
                horizontal=True,
                label_visibility="collapsed",
                key=f"v_{t_id}",
            )
            
        if view_mode == "Table Layout":
            df = pd.DataFrame(docs)
            st.dataframe(df, use_container_width=True, height=600)
        else:
            st.json(docs, expanded=True)
            
    except Exception as e:
        st.error(f"❌ Error fetching documents: {e}")

def main():
    load_css()
    init_session_state()
    render_sidebar()

    if not st.session_state.open_tabs:
        render_empty_state()
    else:
        # Create tabs with nice emojis
        tab_titles = [f"📄 {tab['coll']}" for tab in st.session_state.open_tabs]
        tabs = st.tabs(tab_titles)

        for i, tab_ui in enumerate(tabs):
            with tab_ui:
                render_tab_content(st.session_state.open_tabs[i], i)

if __name__ == "__main__":
    main()
