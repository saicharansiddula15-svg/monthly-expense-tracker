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

# ---------------- CUSTOM CSS FOR EXACT INTERFACE DESIGN ---------------- #
st.markdown("""
    <style>
        /* Base Premium Dark Background */
        .stApp {
            background-color: #0B0F19;
            color: #F8FAFC;
        }
        
        /* Metric Cards matching the layout mockup */
        .dashboard-metric {
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            background: #111827;
            border: 1px solid #1E293B;
        }
        .m-income { border-top: 4px solid #3B82F6; }
        .m-expense { border-top: 4px solid #EF4444; }
        .m-balance { border-top: 4px solid #10B981; }
        .m-budget { border-top: 4px solid #F59E0B; }
        
        /* Typography overrides */
        .metric-lbl { font-size: 13px; color: #94A3B8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-val { font-size: 26px; font-weight: 700; color: #FFFFFF; margin-top: 5px; }
        .metric-trend { font-size: 12px; margin-top: 8px; font-weight: 600; display: flex; align-items: center; }
        
        /* Sidebar layout styling overrides */
        section[data-testid="stSidebar"] {
            background-color: #0D1527 !important;
            border-right: 1px solid #1E293B;
        }
        
        /* Content Panel Boxes */
        .content-card {
            background-color: #111827;
            padding: 22px;
            border-radius: 14px;
            border: 1px solid #1E293B;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        /* Quick Actions grid buttons styling layout */
        .stButton>button {
            border-radius: 8px !important;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- DATABASE SETUP (SQLite) ---------------- #
def get_db_connection():
    return sqlite3.connect("expense_tracker.db", check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            expense_date TEXT,
            category TEXT,
            amount REAL,
            payment_mode TEXT,
            note TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            income_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            income_date TEXT,
            source TEXT,
            amount REAL,
            note TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            user_id INTEGER PRIMARY KEY,
            budget_amount REAL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_financial_totals(user_id):
    conn = get_db_connection()
    df_inc = pd.read_sql_query("SELECT IFNULL(SUM(amount), 0) as total FROM income WHERE user_id=?", conn, params=(user_id,))
    df_exp = pd.read_sql_query("SELECT IFNULL(SUM(amount), 0) as total FROM expenses WHERE user_id=?", conn, params=(user_id,))
    df_bud = pd.read_sql_query("SELECT budget_amount FROM budgets WHERE user_id=?", conn, params=(user_id,))
    conn.close()
    
    saved_budget = float(df_bud["budget_amount"].iloc[0]) if not df_bud.empty else None
    return float(df_inc["total"].iloc[0]), float(df_exp["total"].iloc[0]), saved_budget

# ---------------- SIDEBAR NAVIGATION Panel ---------------- #
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #38BDF8; font-weight:800; margin-bottom:5px;'>EXPENSE TRACKER</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size:12px; color: #64748B; margin-bottom:25px;'>Take Control of Your Finances</p>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        st.markdown("<h4 style='color: #F1F5F9;'>Hello Again! 👋</h4>", unsafe_allow_html=True)
        st.caption("Sign in to continue tracking your transactions.")
        auth_mode = st.radio("Access Mode", ["Login", "Register"], horizontal=True)
        
        with st.form("auth_form_side"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN" if auth_mode == "Login" else "REGISTER", use_container_width=True):
                if username and password:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    if auth_mode == "Login":
                        cursor.execute("SELECT user_id, username FROM users WHERE username=? AND password=?", (username, password))
                        user = cursor.fetchone()
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user[0]
                            st.session_state.username = user[1]
                            st.rerun()
                        else:
                            st.error("Invalid credentials supplied.")
                    else:
                        try:
                            cursor.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, password))
                            conn.commit()
                            st.success("Account created successfully! Switching to login.")
                        except sqlite3.IntegrityError:
                            st.error("Username variant already exists.")
                    conn.close()
                else:
                    st.error("Fields cannot be left blank.")
    else:
        st.markdown(f"<p style='color:#94A3B8;'>Welcome back,</p><h4 style='margin-top:-15px; color:#FFFFFF;'>👑 {st.session_state.username}</h4>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("NAVIGATION", ["📊 Dashboard", "💸 Expense Tracker", "💰 Income Tracker", "👤 Profile Settings"])
        
        st.markdown("---")
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""
            st.rerun()

# ---------------- MAIN DASHBOARD WINDOW ---------------- #
if not st.session_state.logged_in:
    st.info("← Please configure your profile login credentials inside the sidebar frame to access the transactional workspace.")
else:
    total_income_all, total_expense_all, custom_budget = get_financial_totals(st.session_state.user_id)
    
    if custom_budget is not None:
        active_budget_base = custom_budget
    elif "global_reset_done" in st.session_state and st.session_state.global_reset_done:
        active_budget_base = 0.00
    else:
        active_budget_base = 180000.00 if (total_income_all > 0 or total_expense_all > 0) else 0.00
    
    # Header Section
    st.markdown(f"## Dashboard Overview")
    st.markdown(f"<p style='color:#94A3B8; margin-top:-15px;'>Welcome back, {st.session_state.username} 👋</p>", unsafe_allow_html=True)
    
    conn = get_db_connection()

    # --- GLOBAL RESET INTERACTION LOGIC ---
    with st.expander("⚠️ System Data Purge Panel (Reset All Historical Data)"):
        st.warning("Performing this action will clear your entire ledger baseline down to zero, dropping income, expenses, and budget parameters.")
        confirm_purge = st.checkbox("Verify action: Set all previous budget, income, and expenses metrics completely to zero.")
        if st.button("🚨 Purge & Reset Global Data", type="primary", disabled=not confirm_purge, use_container_width=True):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE user_id=?", (st.session_state.user_id,))
            cursor.execute("DELETE FROM income WHERE user_id=?", (st.session_state.user_id,))
            cursor.execute("DELETE FROM budgets WHERE user_id=?", (st.session_state.user_id,))
            conn.commit()
            st.session_state.global_reset_done = True
            st.toast("Database profiles cleared out cleanly.", icon="🧹")
            st.rerun()

    # --- DATAFRAME PARSING & MONTH PREPARATION ---
    db_inc = pd.read_sql_query("SELECT income_date, amount FROM income WHERE user_id=?", conn, params=(st.session_state.user_id,))
    db_exp = pd.read_sql_query("SELECT expense_date, category, amount FROM expenses WHERE user_id=?", conn, params=(st.session_state.user_id,))
    
    months_present = set()
    if not db_inc.empty:
        db_inc['month'] = pd.to_datetime(db_inc['income_date'], errors='coerce').dt.strftime('%b %Y')
        months_present.update(db_inc['month'].dropna().unique())
    if not db_exp.empty:
        db_exp['month'] = pd.to_datetime(db_exp['expense_date'], errors='coerce').dt.strftime('%b %Y')
        months_present.update(db_exp['month'].dropna().unique())
        
    sorted_active_months = sorted(list(months_present), key=lambda x: datetime.strptime(x, '%b %Y') if isinstance(x, str) else datetime.today())
    
    if not sorted_active_months:
        sorted_active_months = [datetime.today().strftime('%b %Y')]

    if menu == "📊 Dashboard":
        st.markdown("### 🔍 Filter Visuals By Month Focus Selection")
        selected_month = st.selectbox("Choose Month focus window:", sorted_active_months, index=len(sorted_active_months)-1)
    else:
        selected_month = datetime.today().strftime('%b %Y')

    current_month_income = db_inc[db_inc['month'] == selected_month]['amount'].sum() if not db_inc.empty else 0.0
    current_month_expense = db_exp[db_exp['month'] == selected_month]['amount'].sum() if not db_exp.empty else 0.0
    current_month_balance = current_month_income - current_month_expense

    # Top Metrics Grid (Filtered Dynamically)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""<div class='dashboard-metric m-income'>
            <div class='metric-lbl'>Total Income ({selected_month})</div>
            <div class='metric-val'>₹ {current_month_income:,.0f}</div>
            <div class='metric-trend' style='color:#10B981;'>▲ Active <span style='color:#64748B; font-weight:normal; margin-left:4px;'>selected filter</span></div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class='dashboard-metric m-expense'>
            <div class='metric-lbl'>Total Expenses ({selected_month})</div>
            <div class='metric-val'>₹ {current_month_expense:,.0f}</div>
            <div class='metric-trend' style='color:#EF4444;'>▼ Active <span style='color:#64748B; font-weight:normal; margin-left:4px;'>selected filter</span></div>
        </div>""", unsafe_allow_html=True)
    with m3:
        bal_color = "#10B981" if current_month_balance >= 0 else "#EF4444"
        st.markdown(f"""<div class='dashboard-metric m-balance'>
            <div class='metric-lbl'>Net Balance ({selected_month})</div>
            <div class='metric-val' style='color:{bal_color};'>₹ {current_month_balance:,.0f}</div>
            <div class='metric-trend' style='color:{bal_color};'>■ Net <span style='color:#64748B; font-weight:normal; margin-left:4px;'>balance delta</span></div>
        </div>""", unsafe_allow_html=True)
    with m4:
        budget_pct = (current_month_expense / active_budget_base * 100) if active_budget_base > 0 else 0
        st.markdown(f"""<div class='dashboard-metric m-budget'>
            <div class='metric-lbl'>Monthly Budget Target</div>
            <div class='metric-val'>₹ {active_budget_base:,.0f}</div>
            <div class='metric-trend' style='color:#F59E0B;'>{budget_pct:.0f}% used <span style='color:#64748B; font-weight:normal; margin-left:4px;'>in {selected_month}</span></div>
        </div>""", unsafe_allow_html=True)

    # --- VIEW 1: GRAPH ANALYTICS ---
    if menu == "📊 Dashboard":
        col_g1, col_g2 = st.columns([3, 2])
        
        with col_g1:
            st.markdown(f"<div class='content-card'><h4>Income vs Expense Overview</h4>", unsafe_allow_html=True)
            
            inc_vals = []
            exp_vals = []
            for m in sorted_active_months:
                i_sum = db_inc[db_inc['month'] == m]['amount'].sum() if not db_inc.empty else 0
                e_sum = db_exp[db_exp['month'] == m]['amount'].sum() if not db_exp.empty else 0
                inc_vals.append(i_sum)
                exp_vals.append(e_sum)
                
            fig, ax = plt.subplots(figsize=(7, 3.8))
            fig.patch.set_facecolor('#111827')
            ax.set_facecolor('#111827')
            
            pos = range(len(sorted_active_months))
            for i, m in enumerate(sorted_active_months):
                alpha_val = 1.0 if m == selected_month else 0.4
                if i == 0:
                    ax.bar(pos[i] - 0.18, inc_vals[i], width=0.35, color='#3B82F6', alpha=alpha_val, label='Income')
                    ax.bar(pos[i] + 0.18, exp_vals[i], width=0.35, color='#EF4444', alpha=alpha_val, label='Expense')
                else:
                    ax.bar(pos[i] - 0.18, inc_vals[i], width=0.35, color='#3B82F6', alpha=alpha_val)
                    ax.bar(pos[i] + 0.18, exp_vals[i], width=0.35, color='#EF4444', alpha=alpha_val)
            
            ax.set_xticks(pos)
            ax.set_xticklabels(sorted_active_months, color='#94A3B8', rotation=15)
            ax.tick_params(colors='#94A3B8', labelsize=9)
            ax.legend(facecolor='#1E293B', edgecolor='none', labelcolor='white')
            ax.grid(color='#1E293B', linestyle=':', alpha=0.6)
            st.pyplot(fig)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_g2:
            st.markdown(f"<div class='content-card'><h4>Expense Breakdown: {selected_month} Only</h4>", unsafe_allow_html=True)
            if not db_exp.empty:
                df_filtered_cat = db_exp[db_exp['month'] == selected_month].groupby('category')['amount'].sum().reset_index()
            else:
                df_filtered_cat = pd.DataFrame()
                
            if not df_filtered_cat.empty and df_filtered_cat['amount'].sum() > 0:
                fig2, ax2 = plt.subplots(figsize=(4, 4))
                fig2.patch.set_facecolor('#111827')
                ax2.set_facecolor('#111827')
                ax2.pie(df_filtered_cat['amount'], labels=df_filtered_cat['category'], autopct='%1.0f%%', startangle=140,
                        textprops={'color': '#F8FAFC', 'fontsize': 9}, colors=['#38BDF8', '#F43F5E', '#10B981', '#F59E0B', '#A855F7'])
                ax2.axis('equal')
                st.pyplot(fig2)
            else:
                st.info(f"No logged expense logs recorded for {selected_month}.")
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
                st.caption("No rows matching query constraints inside database.")
                
        with b_col2:
            st.markdown("<h4>Quick System Actions</h4>", unsafe_allow_html=True)
            qa1, qa2 = st.columns(2)
            if qa1.button("💳 Add Income Log", use_container_width=True):
                st.toast("Switch tabs using the Navigation Pane menu inputs.")
            if qa2.button("🧾 View Data Manifest", use_container_width=True):
                st.toast("Export rules are configured live natively.")

    # --- VIEW 2: EXPENSE ENTRY SYSTEM & BUDGET CONFIG ---
    elif menu == "💸 Expense Tracker":
        st.header("Expense Metric Panel Management")
        
        st.markdown("### ⚙️ Configure Monthly Target Budget Limit")
        with st.form("budget_config_form", clear_on_submit=False):
            b_col, btn_col = st.columns([3, 1])
            existing_budget_val = active_budget_base if active_budget_base > 0 else 0.0
            new_budget_input = b_col.number_input("Set Custom Limit (₹)", min_value=0.0, value=float(existing_budget_val), step=1000.0)
            
            if btn_col.form_submit_button("UPDATE BUDGET CAP", type="secondary", use_container_width=True):
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO budgets (user_id, budget_amount) VALUES (?, ?)", 
                               (st.session_state.user_id, new_budget_input))
                conn.commit()
                st.success(f"Monthly limit successfully locked at ₹{new_budget_input:,.2f}!")
                st.rerun()
                
        st.markdown("---")
        st.markdown("### 💳 Log New Transaction Entry")
        with st.form("new_exp_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            d_in = c1.date_input("Transaction Date", datetime.today())
            cat_in = c2.selectbox("Sector Category", ["Food & Dining", "Transportation", "Shopping", "Bills & Utilities", "Entertainment", "Others"])
            amt_in = c3.number_input("Cost Amount (₹)", min_value=0.0, step=100.0)
            note_in = st.text_input("Operational Notes / Custom Flags")
            
            if st.form_submit_button("ADD NEW TRANSACTION ROW", type="primary"):
                if amt_in > 0:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO expenses(user_id, expense_date, category, amount, payment_mode, note) VALUES(?,?,?,?,?,?)",
                                   (st.session_state.user_id, str(d_in), cat_in, amt_in, "UPI", note_in))
                    conn.commit()
                    if "global_reset_done" in st.session_state:
                        st.session_state.global_reset_done = False
                    st.success("Log array updated cleanly.")
                    st.rerun()

        df_exp_all = pd.read_sql_query(
            "SELECT expense_id, expense_date, category, amount, note FROM expenses WHERE user_id=? ORDER BY expense_id DESC", 
            conn, params=(st.session_state.user_id,)
        )
        
        if not df_exp_all.empty:
            st.markdown("#### Database Registry Log Editor")
            st.caption("💡 Double-click any cell below to directly edit and update your data log records.")
            
            edited_exp_df = st.data_editor(df_exp_all, use_container_width=True, hide_index=True, key="exp_tracker_editor", disabled=["expense_id"])
            
            if st.session_state.exp_tracker_editor and st.session_state.exp_tracker_editor["edited_rows"]:
                cursor = conn.cursor()
                for index, changes in st.session_state.exp_tracker_editor["edited_rows"].items():
                    exp_id = int(df_exp_all.iloc[index]["expense_id"])
                    for key, val in changes.items():
                        cursor.execute(f"UPDATE expenses SET {key}=? WHERE expense_id=?", (val, exp_id))
                conn.commit()
                st.success("Changes saved successfully!")
                st.rerun()

            st.markdown("---")
            st.markdown("##### System Actions")
            confirm_exp_reset = st.checkbox("I authorize the permanent structural deletion of all localized expense rows.")
            if st.button("🚨 Reset All Expenses to Zero", type="secondary", use_container_width=True, disabled=not confirm_exp_reset):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE user_id=?", (st.session_state.user_id,))
                conn.commit()
                st.toast("All expense tracking structures cleared clean.", icon="🗑️")
                st.rerun()

    # --- VIEW 3: INCOME PIPELINE ---
    elif menu == "💰 Income Tracker":
        st.header("Income Inflows Manager")
        
        with st.form("inc_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            d_in = c1.date_input("Inflow Date", datetime.today())
            src_in = c2.text_input("Asset Inflow Stream Source Channel")
            val_in = c3.number_input("Inflow Value Base (₹)", min_value=0.0, step=100.0)
            
            if st.form_submit_button("COMMIT INCOME LOG", type="primary"):
                if val_in > 0 and src_in:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO income(user_id, income_date, source, amount, note) VALUES(?,?,?,?,?)",
                                   (st.session_state.user_id, str(d_in), src_in, val_in, ""))
                    conn.commit()
                    if "global_reset_done" in st.session_state:
                        st.session_state.global_reset_done = False
                    st.success("Income metrics calculated successfully.")
                    st.rerun()
        
        df_inc_all = pd.read_sql_query(
            "SELECT income_id, income_date, source, amount FROM income WHERE user_id=? ORDER BY income_id DESC", 
            conn, params=(st.session_state.user_id,)
        )
        
        if not df_inc_all.empty:
            st.markdown("#### Income Pipeline Register Editor")
            st.caption("💡 Double-click any cell below to directly edit and update your income logs.")
            
            edited_inc_df = st.data_editor(df_inc_all, use_container_width=True, hide_index=True, key="inc_tracker_editor", disabled=["income_id"])
            
            if st.session_state.inc_tracker_editor and st.session_state.inc_tracker_editor["edited_rows"]:
                cursor = conn.cursor()
                for index, changes in st.session_state.inc_tracker_editor["edited_rows"].items():
                    inc_id = int(df_inc_all.iloc[index]["income_id"])
                    for key, val in changes.items():
                        cursor.execute(f"UPDATE income SET {key}=? WHERE income_id=?", (val, inc_id))
                conn.commit()
                st.success("Income dataset records modified successfully!")
                st.rerun()

            st.markdown("---")
            st.markdown("##### System Actions")
            confirm_inc_reset = st.checkbox("I authorize the permanent structural deletion of all localized income records.")
            if st.button("🚨 Reset All Income to Zero", type="secondary", use_container_width=True, disabled=not confirm_inc_reset):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM income WHERE user_id=?", (st.session_state.user_id,))
                conn.commit()
                st.toast("Income structures have successfully dropped down to zero.", icon="📉")
                st.rerun()

    # --- VIEW 4: USER CONTROL ACCOUNT OPTIONS ---
    elif menu == "👤 Profile Settings":
        st.header("Account Configuration Settings")
        st.markdown(f"**Identified Operator Profile:** `{st.session_state.username}`")
        with st.form("update_user_form"):
            new_u = st.text_input("Adjust Flag Username String")
            new_p = st.text_input("Reset Cryptographic Key Account Password", type="password")
            if st.form_submit_button("SAVE ALL SYSTEM SPECIFICATIONS"):
                cursor = conn.cursor()
                if new_u.strip():
                    cursor.execute("UPDATE users SET username=? WHERE user_id=?", (new_u.strip(), st.session_state.user_id))
                    st.session_state.username = new_u.strip()
                if new_p.strip():
                    cursor.execute("UPDATE users SET password=? WHERE user_id=?", (new_p.strip(), st.session_state.user_id))
                conn.commit()
                st.success("Profile configurations customized cleanly.")
                st.rerun()

    conn.close()