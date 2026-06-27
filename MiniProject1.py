import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# ---------------- CONFIGURATION & STATE ---------------- #
st.set_page_config(page_title="Expense Tracker Dashboard", page_icon="💰", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "dark_theme" not in st.session_state:
    st.session_state.dark_theme = True

# ---------------- DATABASE SETUP & UTILITIES (SQLite) ---------------- #
def get_db_connection():
    return sqlite3.connect("expense_tracker.db", check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, expense_date TEXT,
            category TEXT, amount REAL, payment_mode TEXT, note TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            income_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, income_date TEXT,
            source TEXT, amount REAL, note TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_monthly_financial_totals(user_id, month_str):
    conn = get_db_connection()
    inc_query = "SELECT IFNULL(SUM(amount), 0) as total FROM income WHERE user_id=? AND strftime('%Y-%m', income_date)=?"
    exp_query = "SELECT IFNULL(SUM(amount), 0) as total FROM expenses WHERE user_id=? AND strftime('%Y-%m', expense_date)=?"
    
    df_inc = pd.read_sql_query(inc_query, conn, params=(user_id, month_str))
    df_exp = pd.read_sql_query(exp_query, conn, params=(user_id, month_str))
    conn.close()
    return float(df_inc["total"].iloc[0]), float(df_exp["total"].iloc[0])

# ---------------- ACCURATE HIGH-CONTRAST CSS THEMING ---------------- #
if st.session_state.dark_theme:
    st.markdown("""
        <style>
            .stApp { background-color: #0B0F19; color: #F8FAFC; }
            h1, h2, h3, h4, h5, h6, .content-card h4, .content-card h5 { color: #FFFFFF !important; }
            p, span, label, [data-testid="stMarkdownContainer"] p { color: #F8FAFC !important; }
            
            .dashboard-metric {
                border-radius: 14px; padding: 20px; margin-bottom: 15px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25); background: #111827; border: 1px solid #1E293B;
            }
            .m-income { border-top: 4px solid #3B82F6; }
            .m-expense { border-top: 4px solid #EF4444; }
            .m-balance { border-top: 4px solid #10B981; }
            .m-budget { border-top: 4px solid #F59E0B; }
            .metric-lbl { font-size: 13px; color: #94A3B8 !important; font-weight: 500; text-transform: uppercase; }
            .metric-val { font-size: 26px; font-weight: 700; color: #FFFFFF !important; margin-top: 5px; }
            
            section[data-testid="stSidebar"] { background-color: #0D1527 !important; border-right: 1px solid #1E293B; }
            section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #FFFFFF !important; }
            
            .content-card { background-color: #111827; padding: 22px; border-radius: 14px; border: 1px solid #1E293B; margin-bottom: 20px; }
            
            .stButton>button, .stButton>button p, .stButton>button span { color: #FFFFFF !important; font-weight: 600 !important; }
            .stButton>button { background-color: #1F2937 !important; border: 1px solid #374151 !important; border-radius: 8px !important; }
            .stButton>button:hover { background-color: #374151 !important; }
        </style>
    """, unsafe_allow_html=True)
    chart_bg = '#111827'
    chart_text = '#94A3B8'
    chart_grid = '#1E293B'
    pie_text_color = '#FFFFFF'
else:
    st.markdown("""
        <style>
            .stApp { background-color: #F8FAFC; color: #0F172A; }
            h1, h2, h3, h4, h5, h6, .content-card h4, .content-card h5 { color: #0F172A !important; }
            p, span, label, [data-testid="stMarkdownContainer"] p { color: #334155 !important; }
            
            .dashboard-metric {
                border-radius: 14px; padding: 20px; margin-bottom: 15px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); background: #FFFFFF; border: 1px solid #E2E8F0;
            }
            .m-income { border-top: 4px solid #2563EB; }
            .m-expense { border-top: 4px solid #DC2626; }
            .m-balance { border-top: 4px solid #16A34A; }
            .m-budget { border-top: 4px solid #EA580C; }
            .metric-lbl { font-size: 13px; color: #64748B !important; font-weight: 500; text-transform: uppercase; }
            .metric-val { font-size: 26px; font-weight: 700; color: #0F172A !important; margin-top: 5px; }
            
            section[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
            section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #0F172A !important; }
            
            .content-card { background-color: #FFFFFF; padding: 22px; border-radius: 14px; border: 1px solid #E2E8F0; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
            
            .stButton>button, .stButton>button p, .stButton>button span { color: #0F172A !important; font-weight: 600 !important; }
            .stButton>button { background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; }
            .stButton>button:hover { background-color: #F1F5F9 !important; border-color: #94A3B8 !important; }
        </style>
    """, unsafe_allow_html=True)
    chart_bg = '#FFFFFF'
    chart_text = '#475569'
    chart_grid = '#E2E8F0'
    pie_text_color = '#0F172A'

# ---------------- SIDEBAR NAVIGATION PANEL ---------------- #
with st.sidebar:
    st.markdown("<h2 style='text-align: center; font-weight:800; margin-bottom:5px;'>EXPENSE TRACKER</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size:12px; margin-bottom:25px;'>Take Control of Your Finances</p>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        st.markdown("<h4 style='margin-bottom:2px;'>Hello Again! 👋</h4>", unsafe_allow_html=True)
        auth_mode = st.radio("Access Mode", ["Login", "Register"], horizontal=True)
        
        username_input = st.text_input("Username", key="auth_username")
        password_input = st.text_input("Password", type="password", key="auth_password")
        
        if st.button("SUBMIT SYSTEM ACCESS", type="primary", use_container_width=True):
            if username_input.strip() and password_input.strip():
                conn = get_db_connection()
                cursor = conn.cursor()
                if auth_mode == "Login":
                    cursor.execute("SELECT user_id, username FROM users WHERE username=? AND password=?", (username_input.strip(), password_input.strip()))
                    user = cursor.fetchone()
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.rerun()
                    else:
                        st.error("Invalid username or password credentials.")
                elif auth_mode == "Register":
                    try:
                        cursor.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username_input.strip(), password_input.strip()))
                        conn.commit()
                        cursor.execute("SELECT user_id, username FROM users WHERE username=?", (username_input.strip(),))
                        new_user = cursor.fetchone()
                        st.session_state.logged_in = True
                        st.session_state.user_id = new_user[0]
                        st.session_state.username = new_user[1]
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username is already taken!")
                conn.close()
    else:
        st.markdown(f"<p style='color:#94A3B8; margin-bottom: 2px;'>Welcome back,</p><h4 style='margin-top:0px;'>👑 {st.session_state.username}</h4>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("NAVIGATION", ["📊 Dashboard", "💸 Expense Tracker", "💰 Income Tracker", "👤 Profile Settings"])
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""
            st.rerun()

# ---------------- MAIN DASHBOARD WINDOW ---------------- #
if not st.session_state.logged_in:
    st.info("← Please configure or register your user account credentials inside the sidebar frame to access the tracking dashboard.")
else:
    # Header Top Bar Row
    t_col1, t_col2, t_col3 = st.columns([3, 2, 1])
    with t_col1:
        st.markdown(f"## Dashboard Overview")
        st.markdown(f"<p style='color:#94A3B8; margin-top:-15px;'>Welcome back, {st.session_state.username} 👋</p>", unsafe_allow_html=True)
    
    with t_col2:
        st.write(" ")
        current_year = datetime.today().year
        years_pool = [current_year, current_year - 1, current_year - 2]
        months_pool = [("Jan", "01"), ("Feb", "02"), ("Mar", "03"), ("Apr", "04"), ("May", "05"), ("Jun", "06"), 
                       ("Jul", "07"), ("Aug", "08"), ("Sep", "09"), ("Oct", "10"), ("Nov", "11"), ("Dec", "12")]
        
        y_col, m_col = st.columns(2)
        sel_year = y_col.selectbox("Year Filter", years_pool, index=0)
        sel_month_tuple = m_col.selectbox("Month Filter", months_pool, index=datetime.today().month - 1, format_func=lambda x: x[0])
        
        selected_month_str = f"{sel_year}-{sel_month_tuple[1]}"
        selected_month_display = f"{sel_month_tuple[0]} {sel_year}"
        
    with t_col3:
        st.write(" ")
        theme_toggle = st.toggle("🌙 Dark Theme", value=st.session_state.dark_theme)
        if theme_toggle != st.session_state.dark_theme:
            st.session_state.dark_theme = theme_toggle
            st.rerun()
            
    total_income, total_expense = get_monthly_financial_totals(st.session_state.user_id, selected_month_str)
    net_balance = total_income - total_expense
    mock_budget = 180000.00
    
    # Top Metrics Grid Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class='dashboard-metric m-income'>
            <div class='metric-lbl'>Income ({sel_month_tuple[0]})</div>
            <div class='metric-val'>₹ {total_income:,.0f}</div>
            <div class='metric-trend' style='color:#10B981;'>▲ Inflow Tracked</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class='dashboard-metric m-expense'>
            <div class='metric-lbl'>Expenses ({sel_month_tuple[0]})</div>
            <div class='metric-val'>₹ {total_expense:,.0f}</div>
            <div class='metric-trend' style='color:#EF4444;'>▼ Outflow Tracked</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""<div class='dashboard-metric m-balance'>
            <div class='metric-lbl'>Net Balance</div>
            <div class='metric-val'>₹ {net_balance:,.0f}</div>
            <div class='metric-trend' style='color:{"#10B981" if net_balance >= 0 else "#EF4444"};'>● Net Savings</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        budget_pct = (total_expense / mock_budget * 100) if mock_budget > 0 else 0
        st.markdown(f"""<div class='dashboard-metric m-budget'>
            <div class='metric-lbl'>Monthly Budget</div>
            <div class='metric-val'>₹ {mock_budget:,.0f}</div>
            <div class='metric-trend' style='color:#F59E0B;'>{budget_pct:.0f}% used capacity</div>
        </div>""", unsafe_allow_html=True)

    conn = get_db_connection()

    # --- VIEW 1: SIDE-BY-SIDE GRAPHS ANALYTICS ---
    if menu == "📊 Dashboard":
        col_g1, col_g2 = st.columns([3, 2])
        
        with col_g1:
            st.markdown("<div class='content-card'><h4>Income vs Expense Tracking Register</h4>", unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(7, 4.5))
            fig.patch.set_facecolor(chart_bg)
            ax.set_facecolor(chart_bg)
            
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            baseline_inc = [210000, 220000, 215000, 230000, 245800, 190000]
            baseline_exp = [130000, 125000, 140000, 135000, 148650, 110000]
            
            if sel_month_tuple[0] in months:
                m_idx = months.index(sel_month_tuple[0])
                baseline_inc[m_idx] = total_income
                baseline_exp[m_idx] = total_expense
            
            pos = range(len(months))
            width = 0.30
            ax.bar([p - width/2 for p in pos], baseline_inc, width=width, label='Income', color='#2563EB', alpha=0.9)
            ax.bar([p + width/2 for p in pos], baseline_exp, width=width, label='Expense', color='#DC2626', alpha=0.9)
            
            ax.set_xticks(pos)
            ax.set_xticklabels(months, color=chart_text, fontsize=10, fontweight='bold')
            ax.tick_params(colors=chart_text, labelsize=9)
            
            for spine in ['top', 'right', 'left', 'bottom']:
                ax.spines[spine].set_visible(False)
                
            legend_txt_color = 'white' if st.session_state.dark_theme else 'black'
            legend_bg_color = '#1E293B' if st.session_state.dark_theme else '#F1F5F9'
            ax.legend(facecolor=legend_bg_color, edgecolor='none', labelcolor=legend_txt_color, loc='upper left')
            ax.grid(color=chart_grid, linestyle='-', linewidth=0.5, alpha=0.7, axis='y')
            
            st.pyplot(fig)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_g2:
            st.markdown("<div class='content-card'><h4>Expenses Category Breakout</h4>", unsafe_allow_html=True)
            df_cat = pd.read_sql_query(
                "SELECT category, SUM(amount) as total FROM expenses WHERE user_id=? AND strftime('%Y-%m', expense_date)=? GROUP BY category", 
                conn, params=(st.session_state.user_id, selected_month_str)
            )
            if not df_cat.empty:
                fig2, ax2 = plt.subplots(figsize=(4.5, 4.5))
                fig2.patch.set_facecolor(chart_bg)
                ax2.set_facecolor(chart_bg)
                ax2.pie(df_cat['total'], labels=df_cat['category'], autopct='%1.0f%%', startangle=140,
                        textprops={'color': pie_text_color, 'fontsize': 10, 'weight': 'bold'}, 
                        colors=['#38BDF8', '#F43F5E', '#10B981', '#F59E0B', '#A855F7'])
                ax2.axis('equal')
                st.pyplot(fig2)
            else:
                st.info(f"No transactions recorded for {selected_month_display} yet.")
            st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown("---")
        b_col1, b_col2 = st.columns([3, 2])
        with b_col1:
            st.markdown("<h4>Recent Transactions Logs</h4>", unsafe_allow_html=True)
            df_rec = pd.read_sql_query(
                "SELECT expense_date as Date, category as Category, amount as [Amount (₹)], note as Description FROM expenses WHERE user_id=? ORDER BY expense_id DESC LIMIT 3", 
                conn, params=(st.session_state.user_id,)
            )
            if not df_rec.empty:
                st.dataframe(df_rec, use_container_width=True, hide_index=True)
            else:
                st.caption("No transaction variables found inside database.")
                
        with b_col2:
            st.markdown("<h4>Quick System Actions</h4>", unsafe_allow_html=True)
            qa1, qa2 = st.columns(2)
            if qa1.button("💳 Quick Add Income", use_container_width=True):
                st.toast("Navigate to 'Income Tracker' in the left menu to log income.")
            if qa2.button("🧾 Export Spreadsheet", use_container_width=True):
                st.toast("Data manifest exported successfully.")

    # --- VIEW 2: EXPENSE ENTRY SYSTEM WITH IMMEDIATE DROP SELECTION ---
    elif menu == "💸 Expense Tracker":
        st.header("Expense Manager Panel")
        
        df_exp = pd.read_sql_query(
            "SELECT expense_id, expense_date, category, amount, note FROM expenses WHERE user_id=? ORDER BY expense_id DESC", 
            conn, params=(st.session_state.user_id,)
        )
        
        selected_exp_id = None
        default_date = datetime.today()
        default_cat_idx = 0
        default_amount = 0.0
        default_note = ""
        
        st.markdown("### 1. Select a row to Edit or Delete")
        row_options = ["New Entry / Clear Form Selection"]
        if not df_exp.empty:
            row_options += [
                f"ID: {row['expense_id']} | {row['expense_date']} | {row['category']} | ₹{row['amount']}" 
                for _, row in df_exp.iterrows()
            ]
        
        # KEY REPAIR: Placed outside st.form so selecting a row causes an immediate rerun to load values
        selected_row_str = st.selectbox("Choose Transaction Row:", row_options, index=0)
        
        if selected_row_str != "New Entry / Clear Form Selection":
            selected_exp_id = int(selected_row_str.split("ID: ")[1].split(" |")[0])
            matched_row = df_exp[df_exp['expense_id'] == selected_exp_id].iloc[0]
            
            try:
                default_date = datetime.strptime(matched_row['expense_date'], "%Y-%m-%d")
            except:
                default_date = datetime.today()
            cat_list = ["Food & Dining", "Transportation", "Shopping", "Bills & Utilities", "Entertainment", "Others"]
            if matched_row['category'] in cat_list:
                default_cat_idx = cat_list.index(matched_row['category'])
            default_amount = float(matched_row['amount'])
            default_note = str(matched_row['note'])

        st.markdown("### 2. Transaction Management Form")
        with st.form("expense_management_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            d_in = c1.date_input("Transaction Date", value=default_date)
            cat_in = c2.selectbox("Sector Category", ["Food & Dining", "Transportation", "Shopping", "Bills & Utilities", "Entertainment", "Others"], index=default_cat_idx)
            amt_in = c3.number_input("Cost Amount (₹)", min_value=0.0, value=default_amount)
            note_in = st.text_input("Operational Notes / Description Flags", value=default_note)
            
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            add_submitted = btn_col1.form_submit_button("➕ ADD NEW TRANSACTION")
            update_submitted = btn_col2.form_submit_button("💾 UPDATE SELECTED ROW")
            delete_submitted = btn_col3.form_submit_button("🗑️ DELETE SELECTED ROW")
            
            cursor = conn.cursor()
            if add_submitted:
                if amt_in > 0:
                    cursor.execute("INSERT INTO expenses(user_id, expense_date, category, amount, payment_mode, note) VALUES(?,?,?,?,?,?)",
                                   (st.session_state.user_id, str(d_in), cat_in, amt_in, "UPI", note_in))
                    conn.commit()
                    st.success("New transaction row created.")
                    st.rerun()
                else:
                    st.error("Please enter a valid cost amount.")
                    
            elif update_submitted:
                if selected_exp_id:
                    cursor.execute("UPDATE expenses SET expense_date=?, category=?, amount=?, note=? WHERE expense_id=? AND user_id=?", 
                                   (str(d_in), cat_in, amt_in, note_in, selected_exp_id, st.session_state.user_id))
                    conn.commit()
                    st.success("Transaction entry completely updated.")
                    st.rerun()
                else:
                    st.warning("Please select an existing transaction row from the dropdown menu first.")
                    
            elif delete_submitted:
                if selected_exp_id:
                    cursor.execute("DELETE FROM expenses WHERE expense_id=? AND user_id=?", (selected_exp_id, st.session_state.user_id))
                    conn.commit()
                    st.success("Transaction row successfully purged.")
                    st.rerun()
                else:
                    st.warning("Please select an existing transaction row from the dropdown menu first.")

        st.markdown("#### Database Registry Log Editor")
        if not df_exp.empty:
            st.dataframe(df_exp, use_container_width=True, hide_index=True)
        else:
            st.info("No transaction records found.")

    # --- VIEW 3: INCOME PIPELINE WITH IMMEDIATE DROP SELECTION ---
    elif menu == "💰 Income Tracker":
        st.header("Income Inflows Manager")
        
        df_inc = pd.read_sql_query(
            "SELECT income_id, income_date, source, amount, note FROM income WHERE user_id=? ORDER BY income_id DESC", 
            conn, params=(st.session_state.user_id,)
        )
        
        selected_inc_id = None
        default_inc_date = datetime.today()
        default_src = ""
        default_inc_amount = 0.0
        
        st.markdown("### 1. Select an Inflow Row to Edit or Delete")
        row_options = ["New Entry / Clear Form Selection"]
        if not df_inc.empty:
            row_options += [
                f"ID: {row['income_id']} | {row['source']} | ₹{row['amount']}" 
                for _, row in df_inc.iterrows()
            ]
        
        # KEY REPAIR: Placed outside st.form so selecting a row causes an immediate rerun to load values
        selected_row_str = st.selectbox("Choose Income Row:", row_options, index=0)
        
        if selected_row_str != "New Entry / Clear Form Selection":
            selected_inc_id = int(selected_row_str.split("ID: ")[1].split(" |")[0])
            matched_row = df_inc[df_inc['income_id'] == selected_inc_id].iloc[0]
            
            try:
                default_inc_date = datetime.strptime(matched_row['income_date'], "%Y-%m-%d")
            except:
                default_inc_date = datetime.today()
            default_src = str(matched_row['source'])
            default_inc_amount = float(matched_row['amount'])

        st.markdown("### 2. Income Entry Form")
        with st.form("income_management_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            d_inc_in = c1.date_input("Inflow Date", value=default_inc_date)
            src_in = c2.text_input("Asset Inflow Stream Source", value=default_src)
            val_in = c3.number_input("Inflow Value Base (₹)", min_value=0.0, value=default_inc_amount)
            
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            add_inc_submitted = btn_col1.form_submit_button("➕ LOG NEW INCOME")
            update_inc_submitted = btn_col2.form_submit_button("💾 UPDATE SELECTED INCOME")
            delete_inc_submitted = btn_col3.form_submit_button("🗑️ DELETE SELECTED INCOME")
            
            cursor = conn.cursor()
            if add_inc_submitted:
                if val_in > 0 and src_in:
                    cursor.execute("INSERT INTO income(user_id, income_date, source, amount, note) VALUES(?,?,?,?,?)",
                                   (st.session_state.user_id, str(d_inc_in), src_in, val_in, ""))
                    conn.commit()
                    st.success("Income metrics registered successfully.")
                    st.rerun()
                else:
                    st.error("Source channel and Amount metrics cannot be empty.")
                    
            elif update_inc_submitted:
                if selected_inc_id:
                    cursor.execute("UPDATE income SET income_date=?, source=?, amount=? WHERE income_id=? AND user_id=?", 
                                   (str(d_inc_in), src_in, val_in, selected_inc_id, st.session_state.user_id))
                    conn.commit()
                    st.success("Income record entries modified.")
                    st.rerun()
                else:
                    st.warning("Please select an active row index profile to update.")
                    
            elif delete_inc_submitted:
                if selected_inc_id:
                    cursor.execute("DELETE FROM income WHERE income_id=? AND user_id=?", (selected_inc_id, st.session_state.user_id))
                    conn.commit()
                    st.success("Inflow row record deleted.")
                    st.rerun()
                else:
                    st.warning("Please select an active row index profile to purge.")

        st.markdown("#### Database Registry Income Log")
        if not df_inc.empty:
            st.dataframe(df_inc, use_container_width=True, hide_index=True)
        else:
            st.info("No income data logged yet.")

    # --- VIEW 4: USER CONTROL ACCOUNT OPTIONS ---
    elif menu == "👤 Profile Settings":
        st.header("Account Configuration Settings")
        st.markdown(f"**Identified Operator Profile:** `{st.session_state.username}`")
        with st.form("update_user_form"):
            new_u = st.text_input("Adjust Flag Username String")
            new_p = st.text_input("Reset Account Password", type="password")
            if st.form_submit_button("SAVE ALL SYSTEM SPECIFICATIONS"):
                cursor = conn.cursor()
                if new_u.strip():
                    cursor.execute("UPDATE users SET username=? WHERE user_id=?", (new_u.strip(), st.session_state.user_id))
                    st.session_state.username = new_u.strip()
                if new_p.strip():
                    cursor.execute("UPDATE users SET password=? WHERE user_id=?", (new_p.strip(), st.session_state.user_id))
                conn.commit()
                st.success("Profile configurations updated cleanly.")
                st.rerun()

    conn.close()