"""Pocket Ledger - a small, private income and expense tracker.

Run the app with:  streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

from database import (
    add_transaction,
    delete_transaction,
    get_all_transactions,
    initialize_database,
)
from utils.calculations import format_inr

# --- Page setup -----------------------------------------------------------

st.set_page_config(page_title="Pocket Ledger", page_icon="💰", layout="centered")

# A few CSS rules keep the page calm and easy to read.
st.markdown(
    """
    <style>
        .block-container { max-width: 820px; padding-top: 2.5rem; }
        div[data-testid="stForm"] {
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 1.25rem 1.25rem 0.5rem 1.25rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Create data/pocket_ledger.db and the transactions table on first run.
initialize_database()

# Show a short message that survived a page reload (used after deleting).
flash_message = st.session_state.pop("flash", None)
if flash_message:
    st.success(flash_message)

st.title("💰 Pocket Ledger")
st.caption("A simple, private place to track your income and expenses.")

# --- Add a transaction ----------------------------------------------------

with st.form("add_transaction_form", clear_on_submit=True):
    st.subheader("Add a transaction")

    transaction_type = st.radio("Type", ["Expense", "Income"], horizontal=True)

    amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f")

    category = st.text_input("Category", placeholder="e.g. Food, Rent, Salary")

    description = st.text_input(
        "Description (optional)", placeholder="e.g. Lunch with friends"
    )

    transaction_date = st.date_input("Date", value=date.today())

    submitted = st.form_submit_button("Add transaction")

if submitted:
    try:
        add_transaction(
            transaction_type=transaction_type.lower(),
            amount=amount,
            category=category,
            description=description,
            transaction_date=transaction_date.isoformat(),
        )
        # The table is read further down, so the new row appears right away.
        st.success(f"{transaction_type} of {format_inr(amount)} added.")
    except ValueError as error:
        # database.py raises ValueError with a message we can show as-is.
        st.error(str(error))

# --- Show saved transactions ---------------------------------------------

transactions = get_all_transactions()

st.subheader("Your transactions")

if not transactions:
    st.info("No transactions yet. Add your first one above.")
else:
    # Turn the database rows into a Pandas DataFrame for a neat table.
    df = pd.DataFrame([dict(row) for row in transactions])

    display_df = pd.DataFrame(
        {
            "Date": pd.to_datetime(df["transaction_date"]).dt.strftime("%d %b %Y"),
            "Type": df["transaction_type"].str.title(),
            "Category": df["category"],
            "Description": df["description"].fillna(""),
            "Amount": df["amount"].map(format_inr),
        }
    )

    st.dataframe(display_df, hide_index=True)

    # --- Delete a transaction -------------------------------------------

    st.subheader("Delete a transaction")

    # Build a readable label for every transaction, keyed by its database id.
    labels = {
        row["id"]: (
            f"#{row['id']} · {row['transaction_date']} · "
            f"{row['transaction_type'].title()} · {format_inr(row['amount'])} · "
            f"{row['category']}"
        )
        for row in transactions
    }

    # Everything is inside a form so choosing an item does not reset the
    # confirmation checkbox.
    with st.form("delete_transaction_form"):
        selected_id = st.selectbox(
            "Choose a transaction",
            options=list(labels.keys()),
            format_func=lambda transaction_id: labels[transaction_id],
        )

        confirmed = st.checkbox("I understand this cannot be undone")

        delete_clicked = st.form_submit_button("Delete transaction")

    if delete_clicked:
        if not confirmed:
            st.error("Please tick the confirmation box first.")
        elif delete_transaction(selected_id):
            # Store the message, then reload the page so the table refreshes.
            st.session_state["flash"] = "Transaction deleted."
            st.rerun()

st.divider()
st.caption(
    "All data stays in a local SQLite file on this computer. Nothing is uploaded."
)
