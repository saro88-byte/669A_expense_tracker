import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime

DATA_FILE = "online_finance.csv"

# Ensure CSV structure exists
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Description"]).to_csv(DATA_FILE, index=False)

st.set_page_config(layout="wide")
st.title("Saj Family Finance Tracker")

# --- Interactive Filter (Outside Form) ---
t_type = st.radio("Select Transaction Type:", ["Expense", "Income"], horizontal=True)

# --- Form Section ---
with st.form("entry_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        t_date = st.date_input("Date", datetime.today())
    with col2:
        categories = ["Food", "Rent/Utilities", "Transport", "Entertainment", "Shopping", "Other"] if t_type == "Expense" else ["Salary", "Freelance", "Investments", "Other"]
        category = st.selectbox("Category", categories)
    with col3:
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
    with col4:
        description = st.text_input("Description")
        
    submitted = st.form_submit_button("Save Transaction")
    if submitted:
        new_data = pd.DataFrame([[t_date.strftime("%Y-%m-%d"), t_type, category, amount, description]], 
                                columns=["Date", "Type", "Category", "Amount", "Description"])
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Transaction saved successfully!")
        st.rerun()

# --- Data & Visuals Section ---
df = pd.read_csv(DATA_FILE)

if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"])
    df["YearMonth"] = df["Date"].dt.to_period("M")
    available_months = df["YearMonth"].unique().astype(str)
    
    st.markdown("---")
    selected_month = st.selectbox("Filter Visuals by Month", sorted(available_months, reverse=True))
    
    filtered_df = df[df["YearMonth"].astype(str) == selected_month]
    
    # Calculations
    inc = filtered_df[filtered_df["Type"] == "Income"]["Amount"].sum()
    exp = filtered_df[filtered_df["Type"] == "Expense"]["Amount"].sum()
    net = inc - exp
    
    # KPI metrics display
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income", f"${inc:,.2f}")
    c2.metric("Total Expenses", f"${exp:,.2f}")
    c3.metric("Net Profit", f"${net:,.2f}", delta=f"{net:,.2f}")
    
    # Visual Layout Split
    left, right = st.columns(2)
    with left:
        st.subheader(f"Transactions for {selected_month}")
        display_df = filtered_df.copy()
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
        clean_df = display_df.drop(columns=["YearMonth"])
        
        st.info("💡 Double-click any cell below to edit its contents directly!")
        edited_df = st.data_editor(clean_df, use_container_width=True)
        
        # Save and Download Buttons Layout
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("💾 Save Table Edits", type="secondary", use_container_width=True):
                master_df = pd.read_csv(DATA_FILE)
                columns_to_update = ["Date", "Type", "Category", "Amount", "Description"]
                master_df.loc[edited_df.index, columns_to_update] = edited_df[columns_to_update]
                master_df.to_csv(DATA_FILE, index=False)
                st.success("Changes saved successfully!")
                st.rerun()
                
        with btn_col2:
            csv_data = clean_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Download {selected_month} (CSV)",
                data=csv_data,
                file_name=f"finance_data_{selected_month}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
    with right:
        st.subheader("Expense Breakdown")
        exp_df = filtered_df[filtered_df["Type"] == "Expense"]
        
        if not exp_df.empty:
            chart_type = st.selectbox("Choose Chart Type", ["Bar Chart", "Pie Chart"])
            cat_totals = exp_df.groupby("Category")["Amount"].sum().reset_index()
            
            if chart_type == "Bar Chart":
                st.bar_chart(data=cat_totals, x="Category", y="Amount")
            else:
                pie_chart = alt.Chart(cat_totals).mark_arc().encode(
                    theta=alt.Theta(field="Amount", type="quantitative"),
                    color=alt.Color(field="Category", type="nominal"),
                    tooltip=["Category", "Amount"]
                ).properties(height=350)
                st.altair_chart(pie_chart, use_container_width=True)
        else:
            st.write("No expenses logged for this month.")
else:
    st.info("Start tracking by logging your first transaction above!")

# --- Danger Zone (Clear Database with Password Verification) ---
st.markdown("<br><br>", unsafe_allow_html=True) 
with st.expander("⚠️ Danger Zone (Admin ACCESS only)"):
    st.write("Permanently erase all logged items across all history. This cannot be undone.")
    confirm_clear = st.checkbox("I confirm that I want to wipe out the database.")
    
    # Password Field Entry (hidden input characters)
    input_password = st.text_input("Enter Admin Password to verify action:", type="password")
    
    # Check if the user entered the correct updated PIN
    is_password_correct = (input_password == "1111")
    
    # Button only unlocks when confirmed AND password matches perfectly
    button_disabled = not (confirm_clear and is_password_correct)
    
    if st.button("Delete All Records", disabled=button_disabled, type="primary"):
        pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Description"]).to_csv(DATA_FILE, index=False)
        st.success("Database cleared successfully!")
        st.rerun()
    elif confirm_clear and input_password and not is_password_correct:
        st.error("Incorrect password. Please try again.")
