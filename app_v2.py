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
    st.title("🔒 669DASH Finance Tracker - Secure Login")
    
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
    {"Type": "Expense", "Category": "Utilities", "Amount": 210.00, "Description": "Monthly Home Utilities"},
    {"Type": "Expense", "Category": "School Fees", "Amount": 408.50, "Description": "SW School Fees"},
    {"Type": "Expense", "Category": "Internet", "Amount": 60.00, "Description": "Home Fiber Broadband"},
    {"Type": "Expense", "Category": "Phone", "Amount": 138.00, "Description": "Mobile Phone Plan"},
    {"Type": "Expense", "Category": "Domestic Help", "Amount": 735.00, "Description": "Helper"},
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

st.title("669DASH Finance Tracker")

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
                "Apparel & Clothing", "Books", "Dining", "Domestic Help", "Entertainment", "Grocery & Provisions",
                "Household", "Home Loan", "House Maintenance", "Hostel Fees", "Insurance", "Internet", "Investment", 
                "IT Expenses", "Medical", "Motor Vehicle", "Online Purchase", "Petrol", "Phone", "School Fees", 
                "Shopping", "Transportation", "Travel", "Tuition Fees", "Utilities", "Vehicle Loan", "Other"
            ]
        else:
            categories = ["Fixed Income", "Freelance", "Investments", "Interest", "Other"]
            
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
    df["Year"] = df["Date"].dt.year.astype(str)
    df["MonthName"] = df["Date"].dt.strftime("%b")
    df["YearMonth"] = df["Date"].dt.to_period("M")
    
    # ----------------------------------------------------
    # 📅 FEATURE: MONTHLY OVERVIEW BY YEAR
    # ----------------------------------------------------
    st.markdown("---")
    st.header("📅 Monthly Overview by Year")
    
    available_years = sorted(df["Year"].unique(), reverse=True)
    selected_year = st.selectbox("Select Target Year", available_years)
    
    yearly_df = df[df["Year"] == selected_year].copy()
    yearly_df["Type"] = yearly_df["Type"].astype(str).str.strip().str.capitalize()
    
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_summary = yearly_df.groupby(["MonthName", "Type"])["Amount"].sum().unstack(fill_value=0.0)
    
    for t in ["Income", "Expense"]:
        if t not in monthly_summary.columns:
            monthly_summary[t] = 0.0
            
    monthly_summary["Net Savings"] = monthly_summary["Income"] - monthly_summary["Expense"]
    monthly_summary["Savings Rate"] = (monthly_summary["Net Savings"] / monthly_summary["Income"] * 100).fillna(0.0)
    monthly_summary["Savings Rate"] = monthly_summary["Savings Rate"].apply(lambda x: f"{max(0.0, x):.1f}%")
    
    monthly_summary = monthly_summary.reindex(month_order).dropna(how="all").fillna(0.0)
    
    formatted_summary = monthly_summary.copy()
    for col in ["Income", "Expense", "Net Savings"]:
        formatted_summary[col] = formatted_summary[col].apply(lambda x: f"${x:,.2f}")
    
    top_left, top_right = st.columns(2)
    with top_left:
        st.subheader(f"Monthly Trends ({selected_year})")
        trend_grouped = yearly_df.groupby(["MonthName", "Type"])["Amount"].sum().reset_index()
        
        trend_chart = alt.Chart(trend_grouped).mark_bar().encode(
            x=alt.X("MonthName:N", sort=month_order, title="Month"),
            y=alt.Y("Amount:Q", title="Amount ($)"),
            color=alt.Color("Type:N", scale=alt.Scale(domain=["Income", "Expense"], range=["#2ecc71", "#e74c3c"])),
            xOffset="Type:N"
        ).properties(height=280).interactive()
        st.altair_chart(trend_chart, use_container_width=True)
        
    with top_right:
        st.subheader(f"Financial Breakdown ({selected_year})")
        st.dataframe(formatted_summary, use_container_width=True)

    # ----------------------------------------------------
    # 🌙 MONTHLY DETAILS VIEW
    # ----------------------------------------------------
    st.markdown("---")
    st.header("🌙 Monthly Details & Management")
    
    filtered_months = df[df["Year"] == selected_year]["YearMonth"].unique().astype(str)
    selected_month = st.selectbox("Select Month for Detailed Review / Editing", sorted(filtered_months, reverse=True))
    
    filtered_df = df[df["YearMonth"].astype(str) == selected_month]
    
    inc = filtered_df[filtered_df["Type"] == "Income"]["Amount"].sum()
    exp = filtered_df[filtered_df["Type"] == "Expense"]["Amount"].sum()
    net = inc - exp
    savings_rate_display = f"{max(0.0, (net / inc * 100)):.1f}%" if inc > 0 else "0.0%"
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Income", f"${inc:,.2f}")
    c2.metric("Total Expenses", f"${exp:,.2f}")
    c3.metric("Net Profit", f"${net:,.2f}", delta=f"{net:,.2f}")
    c4.metric("Savings Rate", savings_rate_display, delta="Target: >20%" if inc > 0 else None, delta_color="off")
    
    left, right = st.columns(2)
    with left:
        st.subheader(f"Transactions for {selected_month}")
        display_df = filtered_df.copy()
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
        clean_df = display_df.drop(columns=["YearMonth", "Year", "MonthName"])
        
        st.info("💡 Edit cells directly or select a row and press 'Delete' on your keyboard. Click 'Save' below.")
        edited_df = st.data_editor(clean_df, use_container_width=True, num_rows="dynamic")
        
        if st.button("💾 Save Table Changes", type="primary", use_container_width=True):
            master_df = pd.read_csv(DATA_FILE)
            
            visible_indices = clean_df.index
            final_indices = edited_df.index
            deleted_indices = [idx for idx in visible_indices if idx not in final_indices]
            
            if deleted_indices:
                master_df = master_df.drop(index=deleted_indices)
            
            columns_to_update = ["Date", "Type", "Category", "Amount", "Description"]
            
            legacy_edits = edited_df[edited_df.index.isin(master_df.index)]
            new_appends = edited_df[~edited_df.index.isin(master_df.index)]
            
            if not legacy_edits.empty:
                master_df.loc[legacy_edits.index, columns_to_update] = legacy_edits[columns_to_update]
                
            if not new_appends.empty:
                master_df = pd.concat([master_df, new_appends[columns_to_update]], ignore_index=True)
            
            master_df = master_df.sort_values(by="Date").reset_index(drop=True)
            master_df.to_csv(DATA_FILE, index=False)
            st.success("Database file rewritten successfully!")
            st.rerun()
            
    with right:
        st.subheader("Category Expenditure Allocation")
        clean_type_df = filtered_df.copy()
        clean_type_df["Type"] = clean_type_df["Type"].astype(str).str.strip().str.capitalize()
        expense_only = clean_type_df[clean_type_df["Type"] == "Expense"]
        
        if not expense_only.empty:
            base_chart = alt.Chart(expense_only).encode(
                theta=alt.Theta(field="Amount", type="quantitative"),
                color=alt.Color(field="Category", type="nominal", legend=alt.Legend(title="Categories")),
                tooltip=["Category", "Amount"]
            )
            
            donut = base_chart.mark_arc(innerRadius=90, outerRadius=140)
            
            total_expense = expense_only["Amount"].sum()
            text_data = pd.DataFrame([{"text": f"${total_expense:,.2f}"}])
            
            center_text = alt.Chart(text_data).mark_text(
                fontSize=20, 
                fontWeight="bold", 
                color="white" if st.get_option("theme.base") == "dark" else "black"
            ).encode(text="text:N")
            
            final_chart = alt.layer(donut, center_text).properties(height=350)
            st.altair_chart(final_chart, use_container_width=True)
        else:
            st.info("No expense allocation data available for this month.")
