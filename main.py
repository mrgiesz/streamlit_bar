import streamlit as st
import pymysql
import time
from mfrc522 import SimpleMFRC522
from collections import defaultdict
from config import username, password, host, database

# setting up nfc reader
reader = SimpleMFRC522()

# setting page layout
st.set_page_config(layout="wide")
col1, col2, col3 = st.columns(3)


class Product:
    def __init__(self, id, name, cost, visible):
        self.id = id
        self.nr = id - 1
        self.name = name
        self.cost = cost
        self.visible = visible
        self.amount = 0


class User:
    def __init__(self, id, name, badge_uid, wallet):
        self.id = id
        self.name = name
        self.badge_uid = badge_uid
        self.wallet = wallet


def database_connection():
    db = pymysql.connect(host=host,
                         user=username,
                         password=password,
                         database=database)
    return db, db.cursor()


def initial_stuff():
    # PRODUCT SECTION
    # Get products from database
    cursor.execute(queries["products"])
    items = cursor.fetchall()

    # dict containing all the products
    products = {}
    for product_id, product_name, product_cost, visible in items:
        products[product_id] = Product(product_id, product_name, product_cost, visible)

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


def update_users():
    # dict containing all the users
    users = {}

    # Get users details from SQL
    cursor.execute(queries["users"])
    items = cursor.fetchall()

    # put userinfo in list
    for user_id, user_name, user_badge, user_wallet in items:
        users[user_badge] = User(user_id, user_name, user_badge, user_wallet)

    return users


def clean_session():
    st.session_state.selected_products = defaultdict(lambda: 0)


def read_badge():
    id = str(reader.read_id())
    return id


def check_user(badge_id):
    if users[badge_id].name:
        return True
    else:
        return False


def user_transaction(badge_id):
    for i in st.session_state.selected_products:
        if st.session_state.selected_products[i]:
            users = update_users()
            user = users[badge_id]
            product = products[i]
            product.amount = st.session_state.selected_products[i]
            substr_wallet(user, product.amount * product.cost)
    time.sleep(5)
    clean_session()


def substr_wallet(user, cost):
    org_wallet = int(user.wallet)
    # Calculate new wallet amount
    new_wallet = org_wallet - cost

    # Update db data
    cursor.execute(queries["wallet"], (new_wallet, user.id))

    # print new balance
    if new_wallet > 0:
        st.success(f"{user.name}'s balance from {org_wallet*.01} to {new_wallet*.01}")
    else:
        st.error(f"{user.name}'s balance from {org_wallet*.01} to {new_wallet*.01}")
    db.commit()


def update_transactions(user, product):
    # Update db data
    cursor.execute(queries["transaction"], (user.id,
                                            product.id,
                                            (product.cost * product.amount),
                                            product.amount))
    db.commit()


def main_page():
    # creating session variables
    if 'selected_products' not in st.session_state:
        clean_session()

    with col1:
        st.title("Products")

    with col2:
        st.title("selected products")

    with col3:
        st.title("Checkout")
        if st.button('Cancel'):
            clean_session()
        if st.button('Checkout'):
            # load spinner, and wait for badge to be scanned
            with st.spinner("scan badge"):
                badge_id = read_badge()
                # check if user exists in database
                if check_user(badge_id):
                    # start transaction
                    user_transaction(badge_id)

    # run through products
    for i in products:
        # select only the visible products
        if products[i].visible:
            with col1:
                # create buttons for all visible products
                if st.button(products[i].name):
                    st.session_state.selected_products[products[i].id] += 1
            with col2:
                # show selected products in second column
                if st.session_state.selected_products[products[i].id]:
                    st.write(f'{products[i].name} amount: {st.session_state.selected_products[products[i].id]}')


queries = {"products": "SELECT * FROM products", "users": "SELECT * FROM users",
           "transaction": "INSERT INTO transactions(user_id,product_id,transaction_cost,transaction_amount) VALUES ("
                          "%s,%s,%s,%s)",
           "wallet": "UPDATE users SET user_wallet = %s WHERE user_id = %s",
           "register": "INSERT INTO register(user_id,register_amount,register_description) VALUES (%s,%s,%s)"}

# creating global access to db
db, cursor = database_connection()

if __name__ == '__main__':
    products, users = initial_stuff()
    main_page()
