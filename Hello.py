# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger
import requests

LOGGER = get_logger(__name__)

API_URL = "https://api.realestateapi.com/v2/AutoComplete"

def fetch_address_suggestions(query, API_KEY):
    # Only fetch suggestions if the query length is at least 3 characters
    if len(query) < 3:
        return []
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "x-user-id": "ai2-hackathon-2024"
    }
    body = {
        "search": query
    }
    response = requests.post(API_URL, json=body, headers=headers)
    if response.status_code == 200:
        suggestions_data = response.json().get('data', [])
        titles = [suggestion['title'] for suggestion in suggestions_data if 'title' in suggestion]
        #st.write(titles)  # This will display the list of titles in the Streamlit app
        return titles
    else:
        LOGGER.error(f"Failed to fetch suggestions: {response.status_code} - {response.text}")
        return []

def run():
    st.set_page_config(page_title="Team 12", page_icon="👋")
    st.write("# Team 12!")
    API_KEY = st.secrets["API_KEY"]

    # Address input field
    address_input = st.text_input("Enter Property Address", key='address_input')

    selected_address = None

    # Dropdown to show suggestions
    if address_input and len(address_input) >= 3:
        suggestions = fetch_address_suggestions(address_input, API_KEY)
        if suggestions:
            selected_address = st.selectbox("Select an Address", suggestions)
            # Use a separate key for the selectbox to maintain its state independently
            st.session_state['selected_address'] = selected_address


if __name__ == "__main__":
    run()
