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
import pandas as pd

LOGGER = get_logger(__name__)

API_URL = "https://api.realestateapi.com/v2/"

def fetch_address_suggestions(query, headers):
    # Only fetch suggestions if the query length is at least 3 characters
    if len(query) < 3:
        return []

    body = {
        "search": query
    }

    URL = API_URL + "AutoComplete"

    response = requests.post(URL, json=body, headers=headers)
    if response.status_code == 200:
        suggestions_data = response.json().get('data', [])
        titles = [suggestion['title'] for suggestion in suggestions_data if 'title' in suggestion]
        #st.write(titles)  # This will display the list of titles in the Streamlit app
        return titles
    else:
        LOGGER.error(f"Failed to fetch suggestions: {response.status_code} - {response.text}")
        return []

def fetch_rent_estimates(selected_address, headers):
    if selected_address == None:
        return []
    
    select_demographics = ['fmrEfficiency', 'fmrOneBedroom', 'fmrTwoBedroom', 'fmrThreeBedroom', 'fmrFourBedroom']

    URL = API_URL + "PropertyDetail"

    body = {
        "address": selected_address 
    }
    
    response = requests.post(URL, json=body, headers=headers)
    if response.status_code == 200:
        property_data = response.json().get('data', [])

        if "demographics" not in property_data:
            return []

        property_demographics = property_data["demographics"]

        rent_estimates = [property_demographics[select_demographic] for select_demographic in select_demographics if select_demographic in property_demographics]
        #st.write( rent_estimates )

        return rent_estimates
    else:
        LOGGER.error(f"Failed to fetch suggestions: {response.status_code} - {response.text}")
        return []

def run():
    st.set_page_config(page_title="Team 12", page_icon="👋")
    st.write("# Team 12!")
    API_KEY = st.secrets["API_KEY"]
    
    headers = None

    # Headers for API Requests
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "x-user-id": "ai2-hackathon-2024"
    }

    # Address input field
    address_input = st.text_input("Enter Property Address", key='address_input')

    selected_address = None
    demographics = None
    total_monthly_rent = 0

    # Dropdown to show suggestions
    if address_input and len(address_input) >= 3:
        suggestions = fetch_address_suggestions(address_input, headers)
        if suggestions:
            selected_address = st.selectbox("Select an Address", suggestions)
            # Use a separate key for the selectbox to maintain its state independently
            st.session_state['selected_address'] = selected_address

        purchase_price = st.text_input("Purchase Price", key='purchase_price')
        down_payment = st.text_input("Down Payment", key='down_payment')
        closing_costs = st.text_input("Closing Costs", key='closing_costs')
        loan_interest_rate = st.text_input("Loan Interest Rate", key='loan_interest_rate')
        estimated_annual_appriceiation = st.text_input("Estimated Annual Appreciation", key='estimated_annual_appriceiation')
        annual_property_taxes = st.text_input("Annual Property Taxes", key='annual_property_taxes')
        annual_insurance = st.text_input("Annual Insurance", key='annual_insurance')
        management = st.text_input("Management", key='management')
        monthly_maintenance_repair = st.text_input("Monthly Maintenance/Repair", key='monthly_maintenance_repair')
        landscaping = st.text_input("Landscaping", key='landscaping')
        monthly_utilities_expenses = st.text_input("Monthly Utilities Expenses", key='monthly_utilities_expenses')
        monthly_rental_income = st.text_input("Monthly Rental Income", key='monthly_rental_income')

        LOGGER.info( selected_address )

        # Fetch HUD Rent Estimate and Render Monthly Rent Assumptions data editor
        rent_estimates = fetch_rent_estimates( selected_address, headers)

        list_unit_types = ["Efficiency", "One Bedroom", "Two Bedrooms", "Three Bedrooms", "Four Bedrooms" ]
        df_rent_estimates = pd.DataFrame(list(zip(list_unit_types, rent_estimates)),
            columns =['Unit Type', 'Monthly Rent'])
        
        df_rent_estimates['Monthly Rent'] = pd.to_numeric( df_rent_estimates['Monthly Rent'] )
        df_rent_estimates['Unit Count'] = 0

        with st.form("rent_estimate_form"):
            st.subheader("Monthly Rent Assumptions")

            df_rent_estimate_submission = st.data_editor( 
                df_rent_estimates,
                column_config={
                    "Monthly Rent": st.column_config.NumberColumn(
                        format="$%d"
                    )
                },
                disabled=['Unit Type'],
                hide_index=True 
            )


            submit_button_rent = st.form_submit_button("Estimate Rent Income")

            if submit_button_rent:
                df_rent_estimate_submission["Monthly Rent Income"] = df_rent_estimate_submission["Monthly Rent"] * df_rent_estimate_submission["Unit Count"]
                total_monthly_rent = df_rent_estimate_submission["Monthly Rent Income"].sum()

        st.write("Monthly Rent Income: ", total_monthly_rent)

if __name__ == "__main__":
    run()
