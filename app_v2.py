import streamlit as st
import pandas as pd
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
        st.dataframe(clean_df, use_container_width=True)
        
        # Feature 1: Download Monthly Data
        csv_data = clean_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Download {selected_month} Data (CSV)",
            data=csv_data,
            file_name=f"finance_data_{selected_month}.csv",
            mime="text/csv",
        )
        
    with right:
        st.subheader("Expense Breakdown")
        exp_df = filtered_df[filtered_df["Type"] == "Expense"]
        if not exp_df.empty:
            cat_totals = exp_df.groupby("Category")["Amount"].sum()
            st.bar_chart(cat_totals)
        else:
            st.write("No expenses logged for this month.")
else:
    st.info("Start tracking by logging your first transaction above!")

# --- Feature 2: Danger Zone (Clear Database) ---
st.markdown("<br><br>", unsafe_allow_html=True) # Add layout spacing
with st.expander("⚠️ Danger Zone (Admin Actions)"):
    st.write("Permanently erase all logged items across all history. This cannot be undone.")
    confirm_clear = st.checkbox("I confirm that I want to wipe out the database.")
    if st.button("Delete All Records", disabled=not confirm_clear, type="primary"):
        pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Description"]).to_csv(DATA_FILE, index=False)
        st.success("Database cleared successfully!")
        st.rerun()
