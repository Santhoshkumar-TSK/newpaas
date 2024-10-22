import streamlit as st
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt, date
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client['expense_tracker']

# Collections
users_collection = db['users']
expenses_collection = db['expenses']
budgets_collection = db['budgets']

# User Authentication
def signup(username, password):
    if users_collection.find_one({'username': username}):
        st.error("Username already exists.")
    else:
        users_collection.insert_one({'username': username, 'password': password})
        st.success("Signup successful! Please log in.")

def login(username, password):
    user = users_collection.find_one({'username': username})
    if user and user['password'] == password:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.success("Logged in successfully!")
    else:
        st.error("Invalid username or password.")

# Add expense data
def add_expense(username, amount, category, date_input):
    datetime_date = dt.combine(date_input, dt.min.time())
    expenses_collection.insert_one({
        'username': username,
        'amount': amount,
        'category': category,
        'date': datetime_date
    })
    st.success("Expense data added successfully!")

# Get user expense data
def get_user_expenses(username):
    return pd.DataFrame(list(expenses_collection.find({'username': username})))

# Set and get budget
def set_budget(username, budget):
    budgets_collection.update_one(
        {"username": username},
        {"$set": {"budget": budget, "month": dt.now().strftime("%Y-%m")}},
        upsert=True
    )
    st.success("Budget set successfully!")

def get_budget(username):
    return budgets_collection.find_one({"username": username, "month": dt.now().strftime("%Y-%m")})

# Export to CSV
def export_data_to_csv(data, username):
    csv_data = data.to_csv(index=False).encode('utf-8')
    st.download_button(label=f"Download {username}'s Expenses as CSV", data=csv_data, file_name=f"{username}_expense_data.csv", mime='text/csv')

# Streamlit UI
st.title("Expense Tracker")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if st.session_state['logged_in']:
    st.sidebar.write(f"Welcome, {st.session_state['username']}")
    action = st.sidebar.selectbox("Choose an action", ["Add Expense", "View Expenses", "Set Budget", "Logout"])

    if action == "Add Expense":
        st.subheader("Add Expense")
        amount = st.number_input("Amount", min_value=0.01, step=0.01)
        category = st.selectbox("Category", ["Food", "Travel", "Medical", "Education", "Shopping"])
        date_input = st.date_input("Date", value=date.today())
        if st.button("Add Expense"):
            add_expense(st.session_state['username'], amount, category, date_input)

    elif action == "View Expenses":
        st.subheader("Your Expense Data")
        user_expenses = get_user_expenses(st.session_state['username'])
        if not user_expenses.empty:
            user_expenses['date'] = pd.to_datetime(user_expenses['date'])

            # Bar chart of expenses by category
            plt.figure(figsize=(10, 5))
            user_expenses.groupby('category')['amount'].sum().plot(kind='bar', color='skyblue')
            plt.title('Total Expenses by Category')
            plt.xlabel('Category')
            plt.ylabel('Amount')
            st.pyplot(plt)

            export_data_to_csv(user_expenses, st.session_state['username'])
        else:
            st.write("No expenses data available.")

    elif action == "Set Budget":
        st.subheader("Set Monthly Budget")
        budget = st.number_input("Set Budget for the month", min_value=0.01, step=0.01)
        if st.button("Set Budget"):
            set_budget(st.session_state['username'], budget)

        # Display current budget
        user_budget = get_budget(st.session_state['username'])
        if user_budget:
            st.write(f"Current Budget for {user_budget['month']}: {user_budget['budget']}")

    elif action == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.success("Logged out successfully.")

else:
    auth_choice = st.selectbox("Sign In or Sign Up", ["Sign In", "Sign Up"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_choice == "Sign Up":
        if st.button("Sign Up"):
            signup(username, password)
    elif auth_choice == "Sign In":
        if st.button("Sign In"):
            login(username, password)

