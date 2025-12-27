import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import os

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Local Food Wastage Management System",
    layout="wide"
)
DB_PATH = os.path.join(os.path.dirname(__file__), "food_wastage.db")
# --------------------------------------------------
# Database connection
# --------------------------------------------------
def get_connection():
    return sqlite3.connect(DB_PATH)

def fetch_data(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def execute_query(query, params=None):
    conn = get_connection()
    cur = conn.cursor()
    if params:
        cur.execute(query, params)
    else:
        cur.execute(query)
    conn.commit()
    conn.close()

# --------------------------------------------------
# App title
# --------------------------------------------------
st.title("🥗 Local Food Wastage Management System")
st.write("A platform to reduce food wastage by connecting providers with receivers.")

# --------------------------------------------------
# Sidebar navigation
# --------------------------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "View Food Listings",
        "Claims Management",
        "SQL Analysis",
        "Add New Food Listing"
    ]
)

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if page == "Dashboard":
    st.subheader("📊 Dashboard Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Providers",
        fetch_data("SELECT COUNT(*) AS c FROM providers")["c"][0]
    )
    col2.metric(
        "Total Receivers",
        fetch_data("SELECT COUNT(*) AS c FROM receivers")["c"][0]
    )
    col3.metric(
        "Total Food Listings",
        fetch_data("SELECT COUNT(*) AS c FROM food_listings")["c"][0]
    )

    st.divider()

    st.subheader("Food Listings by City")
    city_df = fetch_data("""
        SELECT Location, COUNT(*) AS Listings
        FROM food_listings
        GROUP BY Location
    """)
    st.bar_chart(city_df.set_index("Location"))

# --------------------------------------------------
# VIEW FOOD LISTINGS WITH FILTERS
# --------------------------------------------------
elif page == "View Food Listings":
    st.subheader("🍱 Available Food Listings")

    df = fetch_data("SELECT * FROM food_listings")

    col1, col2, col3 = st.columns(3)

    city = col1.selectbox("City", ["All"] + sorted(df["Location"].unique()))
    food_type = col2.selectbox("Food Type", ["All"] + sorted(df["Food_Type"].unique()))
    meal_type = col3.selectbox("Meal Type", ["All"] + sorted(df["Meal_Type"].unique()))

    if city != "All":
        df = df[df["Location"] == city]
    if food_type != "All":
        df = df[df["Food_Type"] == food_type]
    if meal_type != "All":
        df = df[df["Meal_Type"] == meal_type]

    st.dataframe(df, use_container_width=True)

# --------------------------------------------------
# CLAIMS MANAGEMENT
# --------------------------------------------------
elif page == "Claims Management":
    st.subheader("📦 Food Claims")

    claims_df = fetch_data("""
        SELECT 
            c.Claim_ID,
            f.Food_Name,
            r.Name AS Receiver_Name,
            c.Status,
            c.Timestamp
        FROM claims c
        JOIN food_listings f ON c.Food_ID = f.Food_ID
        JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
    """)

    st.dataframe(claims_df, use_container_width=True)

# --------------------------------------------------
# SQL ANALYSIS (ALL 15 QUERIES)
# --------------------------------------------------
elif page == "SQL Analysis":
    st.subheader("📈 SQL Analysis & Insights")

    queries = {
        "1. Providers count by city":
            "SELECT City, COUNT(*) AS Provider_Count FROM providers GROUP BY City",

        "2. Receivers count by city":
            "SELECT City, COUNT(*) AS Receiver_Count FROM receivers GROUP BY City",

        "3. Provider type contributing most food":
            "SELECT Provider_Type, SUM(Quantity) AS Total_Quantity FROM food_listings GROUP BY Provider_Type",

        "4. Provider contact details":
            "SELECT Name, Type, City, Contact FROM providers",

        "5. Receivers who claimed most food":
            """SELECT r.Name, COUNT(c.Claim_ID) AS Total_Claims
               FROM claims c
               JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
               GROUP BY r.Name
               ORDER BY Total_Claims DESC""",

        "6. Total quantity of food available":
            "SELECT SUM(Quantity) AS Total_Food_Quantity FROM food_listings",

        "7. City with highest food listings":
            "SELECT Location, COUNT(*) AS Listings FROM food_listings GROUP BY Location ORDER BY Listings DESC",

        "8. Most commonly available food types":
            "SELECT Food_Type, COUNT(*) AS Count FROM food_listings GROUP BY Food_Type",

        "9. Number of claims per food item":
            """SELECT f.Food_Name, COUNT(c.Claim_ID) AS Claim_Count
               FROM claims c
               JOIN food_listings f ON c.Food_ID = f.Food_ID
               GROUP BY f.Food_Name""",

        "10. Provider with highest successful claims":
            """SELECT p.Name, COUNT(c.Claim_ID) AS Successful_Claims
               FROM claims c
               JOIN food_listings f ON c.Food_ID = f.Food_ID
               JOIN providers p ON f.Provider_ID = p.Provider_ID
               WHERE c.Status = 'Completed'
               GROUP BY p.Name
               ORDER BY Successful_Claims DESC""",

        "11. Claim status distribution":
            "SELECT Status, COUNT(*) AS Count FROM claims GROUP BY Status",

        "12. Average quantity claimed per receiver":
            """SELECT r.Name, AVG(f.Quantity) AS Avg_Quantity
               FROM claims c
               JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
               JOIN food_listings f ON c.Food_ID = f.Food_ID
               GROUP BY r.Name""",

        "13. Most claimed meal type":
            """SELECT Meal_Type, COUNT(*) AS Claims
               FROM claims c
               JOIN food_listings f ON c.Food_ID = f.Food_ID
               GROUP BY Meal_Type
               ORDER BY Claims DESC""",

        "14. Total food donated by each provider":
            """SELECT p.Name, SUM(f.Quantity) AS Total_Donated
               FROM food_listings f
               JOIN providers p ON f.Provider_ID = p.Provider_ID
               GROUP BY p.Name
               ORDER BY Total_Donated DESC""",

        "15. Expired food items":
            "SELECT Food_Name, Expiry_Date, Location FROM food_listings WHERE Expiry_Date < DATE('now')"
    }

    selected_query = st.selectbox("Select a Query", list(queries.keys()))
    result_df = fetch_data(queries[selected_query])

    st.dataframe(result_df, use_container_width=True)

    if result_df.shape[1] == 2:
        st.bar_chart(result_df.set_index(result_df.columns[0]))

# --------------------------------------------------
# ADD NEW FOOD LISTING (CRUD)
# --------------------------------------------------
elif page == "Add New Food Listing":
    st.subheader("➕ Add New Food Listing")

    with st.form("add_food"):
        food_name = st.text_input("Food Name")
        quantity = st.number_input("Quantity", min_value=1)
        expiry = st.date_input("Expiry Date", min_value=date.today())
        provider_id = st.number_input("Provider ID", min_value=1)
        provider_type = st.text_input("Provider Type")
        location = st.text_input("City")
        food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])

        submit = st.form_submit_button("Add Food")

        if submit:
            execute_query("""
                INSERT INTO food_listings
                (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (food_name, quantity, expiry, provider_id, provider_type, location, food_type, meal_type))

            st.success("Food listing added successfully!")
