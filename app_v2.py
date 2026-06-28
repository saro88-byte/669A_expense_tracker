import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import datetime

DATA_FILE = "online_finance.csv"

st.set_page_config(layout="wide")

# --- FEATURE UPDATE: Secure Public Login Gate ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Saj Family Finance Tracker - Secure Login")
    
    # Simple form wrapper for clean submissions
    with st.form("login_form"):
        password_attempt = st.text_input("Enter Family Access Password:", type="password")
        login_submitted = st.form_submit_button("Access Tracker")
        
        if login_submitted:
            if password_attempt == "1111":
                st.session_state["authenticated"] = True
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Access denied.")
                
    st.stop() # Crucial: Halts execution of all data engines below until logged in

# --- RECURRING MONTHLY DEFAULTS ---
DEFAULT_ITEMS = [
    # Incomes
    {"Type": "Income", "Category": "Salary", "Amount": 13800.00, "Description": "Monthly Fixed Salary"},
    {"Type": "Income", "Category": "Salary", "Amount": 2913.00, "Description": "Monthly Fixed Salary"},
    
    # Expenses
    {"Type": "Expense", "Category": "Rent/Utilities", "Amount": 210.00, "Description": "Monthly Home Utilities"},
    {"Type": "Expense", "Category": "School Fees", "Amount": 408.50, "Description": "Kids School Fees"},
    {"Type": "Expense", "Category": "Internet", "Amount": 60.00, "Description": "Home Fiber Broadband"},
    {"Type": "Expense", "Category": "Phone", "Amount": 138.00, "Description": "Mobile Phone Plan"},
    {"Type": "Expense", "Category": "Other", "Amount": 735.00, "Description": "Helper"},
    {"Type": "Expense", "Category": "Motor Vehicle", "Amount": 110.00, "Description": "Season Parking"},
]

def check_and_add_recurring_items(user_entry_date=None):
    """
    Scans the timeline and ensures defaults exist for the current month,
    the month of any new entry being saved, and any gaps in between.
    """
    df = pd.read_csv(DATA_FILE)
    
    current_month = datetime.today().strftime("%Y-%m")
    target_months = {current_month}
    
    if user_entry_date:
        target_months.add(user_entry_date[:7])
        
    if not df.empty:
        df_months = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m")
        existing_months = set(df_months.values)
        oldest_date_str = df_months.min()
        
        all_periods = pd.period_range(start=oldest_date_str, end=current_month, freq='M').astype(str)
        target_months.update(all_periods)
    else:
        existing_months = set()

    missing_months = sorted(list(target_months - existing_months))
    
    if missing_months:
        new_rows = []
        for month_str in missing_months:
            default_date = f"{month_str}-01"
            for item in DEFAULT_ITEMS:
                new_rows.append([
                    default_date, 
                    item["Type"], 
                    item["Category"], 
                    item["Amount"], 
                    item["Description"]
                ])
                
        recurring_df = pd.DataFrame(new_rows, columns=["Date", "Type", "Category", "Amount", "Description"])
        df = pd.concat([df, recurring_df], ignore_index=True)
        df = df.sort_values(by="Date").reset_index(drop=True)
        df.to_csv(DATA_FILE, index=False)
        st.info(f"✨ Automated recurring items for missing months ({', '.join(missing_months)}) initialized!")

# Ensure CSV structure exists
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Description"]).to_csv(DATA_FILE, index=False)

# Run the automatic recurring items checker on script bootup
check_and_add_recurring_items()

st.title("Saj Family Finance Tracker")

# --- Interactive Filter (Outside Form) ---
t_type = st.radio("Select Transaction Type:", ["Expense", "Income"], horizontal=True)

# --- Form Section ---
with st.form("entry_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        t_date = st.date_input("Date", datetime.today())
    with col2:
        if t_type == "Expense":
            categories = [
                "Apparel & Clothing", "Dining", "Entertainment", "Grocery & Provisions",
                "Household", "Insurance", "Internet", "Medical", "Motor Vehicle",
                "Online Purchase", "Petrol", "Phone", "Rent/Utilities", "School Fees",
                "Shopping", "Tuition Fees", "Other"
            ]
        else:
            categories = ["Salary", "Freelance", "Investments", "Other"]
            
        category = st.selectbox("Category", categories)
    with col3:
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
    with col4:
        description = st.text_input("Description")
        
    submitted = st.form_submit_button("Save Transaction")
    if submitted:
        date_str = t_date.strftime("%Y-%m-%d")
        check_and_add_recurring_items(user_entry_date=date_str)
        
        new_data = pd.DataFrame([[date_str, t_type, category, amount, description]], 
                                columns=["Date", "Type", "Category", "Amount", "Description"])
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
        df = df.sort_values(by="Date").reset_index(drop=True)
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
    
    if inc > 0:
        savings_rate = (net / inc) * 100
        savings_rate_display = f"{max(0.0, savings_rate):.1f}%"
    else:
        savings_rate_display = "0.0%"
    
    # KPI metrics display
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Income", f"${inc:,.2f}")
    c2.metric("Total Expenses", f"${exp:,.2f}")
    c3.metric("Net Profit", f"${net:,.2f}", delta=f"{net:,.2f}")
    c4.metric("Savings Rate", savings_rate_display, delta="Target: >20%" if inc > 0 else None, delta_color="off")
    
    # Visual Layout Split
    left, right = st.columns(2)
    with left:
        st.subheader(f"Transactions for {selected_month}")
        display_df = filtered_df.copy()
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
        clean_df = display_df.drop(columns=["YearMonth"])
        
        st.info("💡 Edit cells directly or select a row and press 'Delete' on your keyboard. Click 'Save' below.")
        edited_df = st.data_editor(clean_df, use_container_width=True, num_rows="dynamic")
        
        # Save and Download Buttons Layout
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("💾 Save Table Changes", type="secondary", use_container_width=True):
                master_df = pd.read_csv(DATA_FILE)
                
                remaining_indices = edited_df.index
                deleted_indices = [idx for idx in clean_df.index if idx not in remaining_indices]
                
                if deleted_indices:
                    master_df = master_df.drop(index=deleted_indices)
                
                columns_to_update = ["Date", "Type", "Category", "Amount", "Description"]
                if not edited_df.empty:
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
        st.subheader("Financial Breakdown")
        chart_type = st.selectbox("Choose Chart Type", ["Bar Chart", "Pie Chart"])
        
        exp_df = filtered_df[filtered_df["Type"] == "Expense"]
        cat_totals = exp_df.groupby("Category")["Amount"].sum().reset_index()
        
        if chart_type == "Bar Chart":
            if not cat_totals.empty:
                st.bar_chart(data=cat_totals, x="Category", y="Amount")
            else:
                st.write("No expenses logged for this month.")
        else:
            # Income-centric Pie Chart Allocation 
            if inc > 0:
                pie_data = cat_totals.copy()
                if net > 0:
                    savings_row = pd.DataFrame([{"Category": "Savings/Balance", "Amount": net}])
                    pie_data = pd.concat([pie_data, savings_row], ignore_index=True)
                
                pie_chart = alt.Chart(pie_data).mark_arc().encode(
                    theta=alt.Theta(field="Amount", type="quantitative"),
                    color=alt.Color(field="Category", type="nominal"),
                    tooltip=["Category", "Amount"]
                ).properties(height=350)
                st.altair_chart(pie_chart, use_container_width=True)
            elif not cat_totals.empty:
                pie_chart = alt.Chart(cat_totals).mark_arc().encode(
                    theta=alt.Theta(field="Amount", type="quantitative"),
                    color=alt.Color(field="Category", type="nominal"),
                    tooltip=["Category", "Amount"]
                ).properties(height=350)
                st.altair_chart(pie_chart, use_container_width=True)
            else:
                st.write("No income or expense records found to generate a pie chart.")
else:
    st.info("Start tracking by logging your first transaction above!")

# --- Danger Zone (Clear Database with Password Verification) ---
st.markdown("<br><br>", unsafe_allow_html=True) 
with st.expander("⚠️ Danger Zone (Admin Actions)"):
    st.write("Permanently erase all logged items across all history. This cannot be undone.")
    confirm_clear = st.checkbox("I confirm that I want to wipe out the database.")
    
    input_password = st.text_input("Enter Admin Password to verify action:", type="password", key="admin_danger_pwd")
    is_password_correct = (input_password == "1111")
    button_disabled = not (confirm_clear and is_password_correct)
    
    if st.button("Delete All Records", disabled=button_disabled, type="primary"):
        pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Description"]).to_csv(DATA_FILE, index=False)
        st.success("Database cleared successfully!")
        st.rerun()
    elif confirm_clear and input_password and not is_password_correct:
        st.error("Incorrect password. Please try again.")
