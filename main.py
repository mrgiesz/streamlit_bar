import streamlit as st
import pymysql
import time
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from collections import defaultdict
from config import username, password, host, database

# setting up nfc reader
reader = SimpleMFRC522()

# setting page layout
col1, col2, col3 = st.columns(3)


class Product:
    def __init__(self, id, name, cost, visible):
        self.id = id
        self.nr = id - 1
        self.name = name
        self.cost = cost
        self.visible = visible
        self.fancy_name = "{:<7}".format(self.name)


class User:
    def __init__(self, id, name, badge_uid, wallet):
        self.id = id
        self.name = name
        self.badge_uid = badge_uid
        self.wallet = wallet


queries = {"products": "SELECT * FROM products", "users": "SELECT * FROM users",
           "transaction": "INSERT INTO transactions(user_id,product_id,transaction_cost,transaction_amount) VALUES ("
                          "%s,%s,%s,%s)",
           "subtraction": "UPDATE users SET user_wallet = %s WHERE id = %s",
           "addition": "INSERT INTO register(user_id,register_amount,register_description) VALUES (%s,%s,%s)"}


def initial_stuff():
    # create database connection
    cursor = database_connection(username, password, host, database)
    # PRODUCT SECTION
    # Get products from database
    cursor.execute(queries["products"])
    items = cursor.fetchall()

    # dict containing all the products
    products = {}
    # Put products in dict
    for nr, (product_id, product_name, product_cost, visible) in enumerate(items):
        products[nr] = Product(product_id, product_name, product_cost, visible)

    # USER SECTION

    # dict containing all the users
    users = {}

    # Get users details from SQL
    cursor.execute(queries["users"])
    items = cursor.fetchall()

    # put userinfo in list
    for user_id, user_name, user_badge, user_wallet in items:
        users[user_badge] = User(user_id, user_name, user_badge, user_wallet)

    return products, users


def database_connection(username, password, host, database):
    db = pymysql.connect(host=host,
                         user=username,
                         password=password,
                         database=database)
    return db.cursor()


def main_page():
    # creating session variables
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = defaultdict(lambda: 0)

    with col1:
        st.title("Products")

    with col2:
        st.title("selected products")
        # st.write(st.session_state)

    with col3:
        st.title("Checkout")
        if st.button('Cancel'):
            st.session_state.selected_products = defaultdict(lambda: 0)
        if st.button('Checkout'):
            with st.spinner("scan badge"):
                id = str(reader.read_id())
                try:
                    st.write(users[id].name)
                    billable_products = st.session_state.selected_products
                    for i in billable_products:
                        if billable_products[i] > 0:
                            st.write(f'{products[i].name} kosten zijn {billable_products[i] * products[i].cost}')
                            st.write(i)
                            st.write(billable_products[i])
                            st.write(products)

                except KeyError:
                    st.write(f'Badge not recognized id is {id}')

    # run through products and create buttons and session items
    for i in products:
        if products[i].visible:

            with col1:
                if st.button(products[i].name):
                    st.session_state.selected_products[products[i].id] += 1
            with col2:
                st.write(
                    f'{products[i].name} amount: {st.session_state.selected_products[products[i].id]}')


if __name__ == '__main__':
    products, users = initial_stuff()
    main_page()
