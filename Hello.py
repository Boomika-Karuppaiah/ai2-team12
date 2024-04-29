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
    
def calculate_monthly_payment(principal, annual_rate, term_years):
    monthly_rate = annual_rate / 12 / 100
    payments = term_years * 12
    monthly_payment = principal * (monthly_rate / (1 - (1 + monthly_rate) ** -payments))
    return monthly_payment

def calculate_debt_reduction(principal, annual_rate, term_years):
    monthly_payment = calculate_monthly_payment(principal, annual_rate, term_years)
    monthly_rate = annual_rate / 12 / 100
    balance = principal
    principal_paid = 0
    
    for month in range(1, 13):  # Calculate for the first year
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        principal_paid += principal_payment
        balance -= principal_payment
    
    return principal_paid

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

        purchase_price = st.number_input("Purchase Price", key='purchase_price')
        down_payment = st.number_input("Down Payment", key='down_payment')
        closing_costs = st.number_input("Closing Costs", key='closing_costs')
        loan_interest_rate = st.number_input("Loan Interest Rate", key='loan_interest_rate')
        estimated_annual_appriceiation = st.number_input("Estimated Annual Appreciation", key='estimated_annual_appriceiation')
        annual_property_taxes = st.number_input("Annual Property Taxes", key='annual_property_taxes')
        annual_insurance = st.number_input("Annual Insurance", key='annual_insurance')
        management = st.number_input("Management", key='management')
        monthly_maintenance_repair = st.number_input("Monthly Maintenance/Repair", key='monthly_maintenance_repair')
        landscaping = st.number_input("Landscaping", key='landscaping')
        monthly_utilities_expenses = st.number_input("Monthly Utilities Expenses", key='monthly_utilities_expenses')
        monthly_rental_income = st.number_input("Monthly Rental Income", key='monthly_rental_income')

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

            analyze_property = st.form_submit_button("Analyze Property")
            if analyze_property:

                st.subheader("Investment Property Analysis")
                st.write("Purchase Price: ",round(float(purchase_price),2))
                st.write((float(down_payment)/float(purchase_price))*100,"% Down Payment: ",round(float(down_payment),2))
                ii = float(down_payment)+float(closing_costs)
                st.write("Initial Investment (Down Payment + Renovation): ",round(ii,2))
                st.write(loan_interest_rate,"% Loan at 30 year fixed rate: ",round(float(purchase_price)-float(down_payment),2))
                monthly_interest_rate = float(loan_interest_rate) / 1200 
                total_payments = 30 * 12  # 30 years * 12 months
                loan_amount = float(purchase_price) - float(down_payment)
                monthly_payment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -total_payments)
                st.write("Monthly Principal & Interest Payments: $", round(monthly_payment*-1,2))
                mtip = (float(annual_property_taxes)+float(annual_insurance))/12*-1
                st.write("Monthly Tax & Insurance Payments: $",round( mtip,2))
                m = float(management)*-1
                st.write("Management: $",round( m,2))
                mmru = (float(monthly_maintenance_repair)+float(landscaping)+float(monthly_utilities_expenses))*-1
                st.write("Monthly Maintenance/Repairs/Utilities: $",round( mmru,2))
                st.write("Monthly Rent Income: ", round(float(monthly_rental_income),2))
                tme = monthly_payment*-1+mtip+m+mmru
                st.write("Total Monthly Expenses: ", round(tme,2))
                mcf = float(monthly_rental_income)+tme
                st.write("Monthly Cash Flow: ", round(mcf,2))

                st.subheader("Returns")
                st.write("Cash Flow - Cash on Cash Return")
                st.write("\$",round((mcf)*12,2)," per year. ROI: \$", round((mcf)*12,2)," / $",ii," = ",round(((mcf)*12)*100/(ii),2),"%")
                st.write("Cap Rate")
                st.write(round((mtip+m+mmru+float(monthly_rental_income))*1200/(float(purchase_price)+(ii-float(down_payment))),2),"%")
                st.write("Debt Reduction")
                principal = float(purchase_price) - float(down_payment)
                debt_reduction = calculate_debt_reduction(principal, float(loan_interest_rate), 30)
                st.write("\$",round(debt_reduction,2),"in principal reduction over the first year.  Your tenant is buying the property and giving it to you at the end of the loan! ")
                st.write("ROI: \$",round(debt_reduction,2), " / $",ii," = ", round(debt_reduction*100/ii,2), "%")
                st.write("Depreciation")
                st.write("$", round(float(purchase_price)*0/27.5,2),"approximate depreciation per year (assuming 0% depreciable and 27.5 year straight line depreciation).  Your rental income may not be subject to tax.")
                st.write("Appreciation")
                appr = float(purchase_price)*float(estimated_annual_appriceiation)/100
                st.write("$", round(appr,2)," is the amount of annual appreciation your property is projected to gain.")
                st.write("ROI: \$",round(appr,2), " / $",ii," = ", round(appr*100/ii,2), "%")

                st.subheader("Summarized Return on Investment After Year 1")
                st.write(round(((mcf)*12)*100/(ii),2),"%","      $",round((mcf)*12,2),"       Cash Flow")
                st.write(round(debt_reduction*100/ii,2),"%","      $",round(debt_reduction,2),"       Debt Reduction")
                st.write(round(appr*100/ii,2),"%","      $",round(appr,2),"       Appreciation")
                st.subheader(str(round(((mcf)*12)*100/(ii)+debt_reduction*100/ii+appr*100/ii,2))+"%    \$"+str(round((mcf)*12+debt_reduction+appr,2))+"     Total Return on Investment for Year 1")


if __name__ == "__main__":
    run()
