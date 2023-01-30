import streamlit as st
import pymysql
import time
# from mfrc522 import SimpleMFRC522
from collections import defaultdict
from config import username, password, host, database

# setting up nfc reader
# reader = SimpleMFRC522()

# setting page layout
st.set_page_config(layout="wide", page_title="Bar")
col_products, col_checkout = st.columns(2)


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

    # put userinfo in dict
    for user_id, user_name, user_badge, user_wallet in items:
        users[user_badge] = User(user_id, user_name, user_badge, user_wallet)

    return products, users


def main_page():
    # creating session variables
    if 'selected_products' not in st.session_state:
        clean_session()

    with col_products:
        st.title("Products")

    with col_checkout:
        st.title("Checkout")


def clean_session():
    st.session_state.selected_products = defaultdict(lambda: 0)


# def read_badge():
#     id = str(reader.read_id())
#     return id


def check_user(badge_id):
    if users[badge_id].name:
        return True
    else:
        return False


def user_transaction(badge_id):
    transaction_cost = 0
    for i in st.session_state.selected_products:
        if st.session_state.selected_products[i]:
            user = users[badge_id]
            product = products[i]
            product.amount = st.session_state.selected_products[i]
            transaction_cost = transaction_cost + (product.amount * product.cost)
            update_transactions(user, product)
    substr_wallet(user, transaction_cost)
    clean_session()
    st.experimental_rerun()


def substr_wallet(user, cost):
    org_wallet = int(user.wallet)
    # Calculate new wallet amount
    new_wallet = org_wallet - cost

    # Update db data
    cursor.execute(queries["wallet"], (new_wallet, user.id))
    db.commit()

    # print new balance
    placeholder = st.empty()

    if new_wallet > 0:
        placeholder.success(
            f"{user.name}'s balance from \u20ac {org_wallet * .01:.2f} to \u20ac {new_wallet * .01:.2f}")
    else:
        placeholder.error(f"{user.name}'s balance from \u20ac {org_wallet * .01:.2f} to \u20ac {new_wallet * .01:.2f}")
    time.sleep(2)
    placeholder.empty()


def update_transactions(user, product):
    # Update db data
    cursor.execute(queries["transaction"], (user.id,
                                            product.id,
                                            (product.cost * product.amount),
                                            product.amount))
    db.commit()


def get_users_dict():
    userdict = {}
    for i in users:
        userdict[users[i].name] = users[i].badge_uid
    return userdict


# def scan_nfc():
#     with st.spinner("scan badge"):
#         badge_id = read_badge()
#         # check if user exists in database
#         if check_user(badge_id):
#             # start transaction
#             user_transaction(badge_id)

def product_column():
    for i in products:
        # select only the visible products
        if products[i].visible:
            with col_products:
                # create buttons for all visible products
                button_name = f'{st.session_state.selected_products[products[i].id]} {products[i].name}'
                if st.button(button_name):
                    st.session_state.selected_products[products[i].id] += 1
                    st.experimental_rerun()
                # uncommend below sections to use sliders
                # st.session_state.selected_products[products[i].id] = st.slider(products[i].name,
                #                                                               min_value=0,
                #                                                               max_value=5,
                #                                                               value=st.session_state.selected_products[
                #                                                                   products[i].id])


def checkout_column():
    with col_checkout:
        userdict = get_users_dict()
        # with st.expander('checkout without nfc tag'):
        chosen_user = st.selectbox("select user", sorted(userdict.keys()))
        if st.button('Checkout'):
            user_transaction(userdict[chosen_user])

        if st.button('Cancel'):
            clean_session()
        # if st.button('Scan NFC'):
        #     # load spinner, and wait for badge to be scanned
        #     scan_nfc()


# General queries variable.
queries = {"products": "SELECT * FROM products", "users": "SELECT * FROM users",
           "transaction": "INSERT INTO transactions(user_id,product_id,transaction_cost,transaction_amount) VALUES ("
                          "%s,%s,%s,%s)",
           "wallet": "UPDATE users SET user_wallet = %s WHERE user_id = %s",
           "register": "INSERT INTO register(user_id,register_amount,register_description) VALUES (%s,%s,%s)"}

# creating global access to db
db, cursor = database_connection()

if __name__ == '__main__':
    # get main variables
    products, users = initial_stuff()
    # create main page layout
    main_page()
    # create product column
    product_column()
    # create checkout column
    checkout_column()
