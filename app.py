import streamlit as st
import pandas as pd
import json
import os
import time
import re
from datetime import datetime
import google.generativeai as genai

# ==========================================
# 🔑 CONFIGURATION
# ==========================================
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# Configure Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"Error configuring Gemini: {e}")

# ==========================================
# 🎨 CUSTOM CSS
# ==========================================

def load_custom_styles():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(to bottom right, #0f0c29, #302b63, #24243e);
            color: #E0E0E0;
        }
        
        /* Navbar Buttons */
        div[data-testid="stHorizontalBlock"] button {
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #d1c4e9;
            border-radius: 12px;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        div[data-testid="stHorizontalBlock"] button:hover {
            background-color: #d1c4e9;
            color: #311b92;
            border-color: #fff;
            box-shadow: 0 0 15px rgba(209, 196, 233, 0.4);
        }

        /* Sidebar User Card */
        .user-card {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }

        /* Product Cards */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
            background-color: rgba(20, 20, 35, 0.8); 
            border-radius: 12px;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease;
            height: 100%;
        }
        div[data-testid="column"]:hover div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
             transform: translateY(-3px);
             border-color: rgba(124, 58, 237, 0.5);
        }
        
        /* Category Pill */
        .category-pill {
            background: rgba(124, 58, 237, 0.3);
            color: #ddd6fe;
            padding: 2px 10px;
            border-radius: 15px;
            font-size: 0.7rem;
            border: 1px solid rgba(124, 58, 237, 0.5);
            display: inline-block;
            margin-bottom: 8px;
        }

        /* Price Tag */
        .price-tag {
            font-size: 1.2rem;
            font-weight: 700;
            color: #34d399;
            margin: 8px 0;
        }

        /* Quantity Display */
        .qty-display {
            text-align: center;
            font-weight: bold;
            font-size: 1.1rem;
            padding-top: 5px;
        }
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255,255,255,0.05);
            border-radius: 10px 10px 0 0;
            color: white;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(124, 58, 237, 0.3);
            border-bottom: 2px solid #7c3aed;
        }
        
        /* Order Table Header */
        .order-header {
            background-color: rgba(124, 58, 237, 0.2);
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            color: #d1c4e9;
            margin-bottom: 10px;
        }
        
        /* Order Row */
        .order-row {
            background-color: rgba(255, 255, 255, 0.02);
            padding: 10px;
            border-radius: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 5px;
            align-items: center;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 📂 PART 1: DATA MANAGER
# ==========================================


class DataManager:
    PRODUCT_FILE = "products.json"
    HISTORY_FILE = "purchase_history.json"

    @staticmethod
    def load_data():
        products = []
        history = []
        if os.path.exists(DataManager.PRODUCT_FILE):
            try:
                with open(DataManager.PRODUCT_FILE, 'r') as f:
                    products = json.load(f)
            except:
                pass
        if os.path.exists(DataManager.HISTORY_FILE):
            try:
                with open(DataManager.HISTORY_FILE, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        return products, history

    @staticmethod
    def save_order(cart_items):
        _, history = DataManager.load_data()
        new_order_id = f"ORD-{int(time.time())}"
        current_date = datetime.now().strftime("%Y-%m-%d")

        new_records = []
        for item in cart_items:
            record = {
                "order_id": new_order_id,
                "item": f"{item['name']} (x{item['qty']})",
                "date": current_date,
                "price": item['price'] * item['qty'],
                "status": "Processing"
            }
            new_records.append(record)
            history.append(record)

        try:
            with open(DataManager.HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=4)
            return True
        except Exception as e:
            st.error(f"Failed to save: {e}")
            return False

    @staticmethod
    def delete_order(order_id_to_remove):
        _, history = DataManager.load_data()
        updated_history = [
            h for h in history if h['order_id'] != order_id_to_remove]
        try:
            with open(DataManager.HISTORY_FILE, 'w') as f:
                json.dump(updated_history, f, indent=4)
            return True
        except:
            return False

# ==========================================
# 🤖 PART 2: AI LOGIC (UPDATED FOR CART)
# ==========================================


def get_ai_response(query, chat_history_str):
    prod, hist = DataManager.load_data()
    cart_txt = json.dumps(
        st.session_state.cart) if 'cart' in st.session_state else "Empty"

    # Context with specialized instructions for JSON output
    context = f"""
    You are Aura, the AI agent for Dream Spells.
    User: Ishara Stanley.
    Cart: {cart_txt}
    History: {json.dumps(hist)}
    Catalog: {json.dumps(prod)}
    Current Conversation History: {chat_history_str}

    *** IMPORTANT CART INSTRUCTIONS ***
    1. If the user asks about a product, describe it briefly and ask: "Do you want to add this to your cart?"
    2. If the user says "Yes" or agrees, ask: "How many would you like?"
    3. If the user provides a number (Quantity) for a specific item discussed, YOU MUST OUTPUT ONLY JSON.
    
    JSON FORMAT FOR ADDING TO CART:
    {{ "action": "add_to_cart", "item_name": "Exact Product Name from Catalog", "qty": Integer }}

    Example: User says "2", you output: {{ "action": "add_to_cart", "item_name": "Heavenly Hues", "qty": 2 }}
    
    For all other normal conversation, just reply with text (no JSON).
    """
    try:
        response = model.generate_content(f"{context}\nUser Input: {query}")
        return response.text
    except:
        return "The spirits are quiet today."


# ==========================================
# ⚙️ PART 3: CALLBACKS
# ==========================================
if "cart" not in st.session_state:
    st.session_state.cart = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Welcome back, Ishara! Ask me about dreamcatchers."}]


def add_to_cart_callback(product, qty_key):
    qty = st.session_state[qty_key]
    found = False
    for item in st.session_state.cart:
        if item['id'] == product['id']:
            item['qty'] += qty
            found = True
            break
    if not found:
        st.session_state.cart.append({
            "id": product['id'],
            "name": product['name'],
            "price": product['price'],
            "qty": qty,
            "image": product['image']
        })
    st.toast(f"Added {qty} {product['name']} to cart!", icon="🛒")


def clear_cart_callback():
    st.session_state.cart = []


def remove_item_callback(index):
    st.session_state.cart.pop(index)


def clear_chat_callback():
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Chat cleared. How can I help?"}]


def update_qty_callback(key, change):
    if key in st.session_state:
        new_val = st.session_state[key] + change
        if 1 <= new_val <= 10:
            st.session_state[key] = new_val


def cancel_order_callback(order_id):
    if DataManager.delete_order(order_id):
        st.toast(f"Order {order_id} Cancelled", icon="🗑️")
    else:
        st.error("Failed to cancel order.")

# ==========================================
# 🖼️ PART 4: POPUPS (Chat & Cart Only)
# ==========================================


@st.dialog("🛒 Your Cart", width="medium")
def open_cart_popup():
    if not st.session_state.cart:
        st.info("Your cart is empty. Go add some magic!")
        return
    c_head1, c_head2 = st.columns([4, 1])
    with c_head1:
        st.write(f"Items: **{len(st.session_state.cart)}**")
    with c_head2:
        st.button("🗑️ Empty", on_click=clear_cart_callback,
                  use_container_width=True)
    st.divider()

    total_amount = 0
    for i, item in enumerate(st.session_state.cart):
        c1, c2, c3, c4 = st.columns([1, 3, 1.5, 0.5])
        with c1:
            if os.path.exists(item['image']):
                st.image(item['image'], width=50)
            else:
                st.write("📷")
        with c2:
            st.markdown(f"**{item['name']}**")
            st.caption(f"x {item['qty']}")
        with c3:
            line_total = item['price'] * item['qty']
            total_amount += line_total
            st.write(f"LKR {line_total}")
        with c4:
            st.button("❌", key=f"del_{i}",
                      on_click=remove_item_callback, args=(i,))
        st.divider()

    col_total, col_checkout = st.columns([2, 1])
    with col_total:
        st.markdown(f"### Total: LKR {total_amount}")
    with col_checkout:
        if st.button("✅ Checkout", type="primary", use_container_width=True):
            if DataManager.save_order(st.session_state.cart):
                st.session_state.cart = []
                st.balloons()
                st.success("Order Placed!")
                time.sleep(1.5)
                st.rerun()


@st.dialog("✨ Chat with Aura", width="small")
def open_chat_popup():
    c1, c2 = st.columns([4, 1])
    with c1:
        st.caption("Ask about products...")
    with c2:
        st.button("🗑️ Clear", help="Clear", on_click=clear_chat_callback)

    chat_container = st.container(height=350)
    for msg in st.session_state.chat_history:
        avatar = "🔮" if msg["role"] == "assistant" else "👤"
        with chat_container.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask Aura..."):
        st.session_state.chat_history.append(
            {"role": "user", "content": prompt})
        with chat_container.chat_message("user", avatar="👤"):
            st.write(prompt)

        with chat_container.chat_message("assistant", avatar="🔮"):
            with st.spinner("..."):
                # Prepare context string from history
                history_str = "\n".join(
                    [f"{m['role']}: {m['content']}" for m in st.session_state.chat_history[-5:]])
                reply = get_ai_response(prompt, history_str)

                # --- NEW: CHECK FOR JSON COMMAND ---
                try:
                    # Simple extraction if the model wraps code
                    clean_reply = reply.replace(
                        "```json", "").replace("```", "").strip()
                    if clean_reply.startswith("{"):
                        command = json.loads(clean_reply)
                        if command.get("action") == "add_to_cart":
                            # Execute Add to Cart
                            target_name = command.get("item_name")
                            target_qty = int(command.get("qty", 1))

                            # Find Product Object
                            products, _ = DataManager.load_data()
                            product_obj = next(
                                (p for p in products if p["name"] == target_name), None)

                            if product_obj:
                                # Add directly to session state cart
                                found = False
                                for item in st.session_state.cart:
                                    if item['id'] == product_obj['id']:
                                        item['qty'] += target_qty
                                        found = True
                                        break
                                if not found:
                                    st.session_state.cart.append({
                                        "id": product_obj['id'],
                                        "name": product_obj['name'],
                                        "price": product_obj['price'],
                                        "qty": target_qty,
                                        "image": product_obj['image']
                                    })
                                success_msg = f"✨ I have added **{target_qty} x {target_name}** to your cart!"
                                st.write(success_msg)
                                st.session_state.chat_history.append(
                                    {"role": "assistant", "content": success_msg})
                                # Allow UI update
                                time.sleep(1)
                                # st.rerun()
                            else:
                                err_msg = "I couldn't find that item in the catalog."
                                st.write(err_msg)
                                st.session_state.chat_history.append(
                                    {"role": "assistant", "content": err_msg})
                        else:
                            # JSON but not add_to_cart
                            st.write(reply)
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": reply})
                    else:
                        # Normal Text Reply
                        st.write(reply)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": reply})
                except Exception as e:
                    # Fallback if JSON parsing fails
                    st.write(reply)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": reply})


# ==========================================
# 🖥️ PART 5: MAIN UI
# ==========================================
st.set_page_config(page_title="Dream Spells Store",
                   page_icon="images/logo/logo.png", layout="wide")
load_custom_styles()

with st.sidebar:
    if os.path.exists("images/logo/logo.png"):
        # Create 3 columns (Spacer | Logo | Spacer) to center it
        _, col_logo, _ = st.columns([1, 2, 1])
        with col_logo:
            st.image("images/logo/logo.png", use_container_width=True)
    else:
        st.markdown("## 🧿 Dream Spells")
        
    st.divider()
        
    st.markdown("""
        <div class="user-card">
            <div style="font-size: 3rem;">👤</div>
            <h3>Ishara Stanley</h3>
            <p style="color:#aaa;">Premium Member</p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("✨ Ask Aura AI", use_container_width=True):
        open_chat_popup()
    st.divider()
    st.info("📍 Shipping to: Kandy, LK")

# --- HEADER & CART BUTTON ---
c_title, c_cart = st.columns([6, 1.2])
with c_title:
    st.title("Dream Spells Collection")
with c_cart:
    cart_count = sum(item['qty'] for item in st.session_state.cart)
    cart_label = f"🛒 Cart ({cart_count})" if cart_count > 0 else "🛒 Cart"
    if st.button(cart_label, use_container_width=True):
        open_cart_popup()

st.write("")

# --- TABS FOR SHOP, ORDERS, STATS ---
tab1, tab2, tab3 = st.tabs(["🛍️ Shop", "📦 Orders", "📊 Spending Stats"])

# === TAB 1: SHOP ===
with tab1:
    products, _ = DataManager.load_data()
    if products:
        cats = ["All"] + sorted(list(set(p['category'] for p in products)))
        sel_cat = st.selectbox("Filter:", cats)
        filtered = products if sel_cat == "All" else [
            p for p in products if p['category'] == sel_cat]
        st.write("")

        cols = st.columns(3)
        for i, p in enumerate(filtered):
            with cols[i % 3]:
                with st.container():
                    if os.path.exists(p.get('image', '')):
                        st.image(p['image'], use_container_width=True)
                    else:
                        st.markdown(
                            "<div style='height:150px; background:rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)

                    st.markdown(
                        f"<span class='category-pill'>{p.get('category')}</span>", unsafe_allow_html=True)
                    st.subheader(p.get('name'))
                    st.caption(p.get('desc')[:500] + "...")
                    st.markdown(
                        f"<div class='price-tag'>LKR {p.get('price')}</div>", unsafe_allow_html=True)

                    c_qty, c_add = st.columns([1.5, 1.5])
                    qty_key = f"qty_{p['id']}"
                    if qty_key not in st.session_state:
                        st.session_state[qty_key] = 1

                    with c_qty:
                        b_minus, b_val, b_plus = st.columns(
                            [1, 1, 1], gap="small")
                        with b_minus:
                            st.button(
                                "➖", key=f"dec_{p['id']}", on_click=update_qty_callback, args=(qty_key, -1))
                        with b_val:
                            st.markdown(
                                f"<div class='qty-display'>{st.session_state[qty_key]}</div>", unsafe_allow_html=True)
                        with b_plus:
                            st.button(
                                "➕", key=f"inc_{p['id']}", on_click=update_qty_callback, args=(qty_key, 1))

                    with c_add:
                        st.button("Add to Cart", key=f"btn_{p['id']}", on_click=add_to_cart_callback, args=(
                            p, qty_key), use_container_width=True)
    else:
        st.error("Catalog not loaded.")

# === TAB 2: ORDERS (Proper Table Layout & Logic) ===
with tab2:
    st.subheader("Order History")
    _, history = DataManager.load_data()

    if history:
        cols = st.columns([1.5, 2.5, 1.5, 1.5, 1.5, 1])
        headers = ["Ref ID", "Items", "Date", "Price", "Status", "Action"]
        for col, h in zip(cols, headers):
            col.markdown(
                f"<div style='font-weight:bold; color:#d1c4e9;'>{h}</div>", unsafe_allow_html=True)

        st.markdown(
            "<hr style='margin:5px 0; border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

        for order in reversed(history):
            c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2.5, 1.5, 1.5, 1.5, 1])

            status = order.get('status', 'Processing')
            status_color = "#FFA726"  # Orange
            can_cancel = False

            if status == "Shipped":
                status_color = "#29B6F6"
            elif status == "Delivered":
                status_color = "#66BB6A"
            elif status == "Processing":
                can_cancel = True

            with c1:
                st.write(order['order_id'])
            with c2:
                st.write(order['item'])
            with c3:
                st.write(order['date'])
            with c4:
                st.write(f"LKR {order['price']}")
            with c5:
                st.markdown(
                    f"<span style='color:{status_color}; font-weight:bold;'>{status}</span>", unsafe_allow_html=True)

            with c6:
                if can_cancel:
                    st.button("Cancel", key=f"cancel_{order['order_id']}", help="Cancel Order", on_click=cancel_order_callback, args=(
                        order['order_id'],))
                elif status == "Delivered":
                    st.write("✅")
                elif status == "Shipped":
                    st.write("🚚")
                else:
                    st.write("-")

            st.markdown(
                "<div style='border-bottom:1px solid rgba(255,255,255,0.05); margin-bottom:5px;'></div>", unsafe_allow_html=True)
    else:
        st.info("No orders placed yet.")

# === TAB 3: STATS (Personal Spending) ===
with tab3:
    st.subheader("My Spending Habits")
    _, history = DataManager.load_data()

    if history:
        df_hist = pd.DataFrame(history)
        df_hist['price'] = pd.to_numeric(df_hist['price'])

        total_spent = df_hist['price'].sum()
        total_orders = len(df_hist)

        c1, c2 = st.columns(2)
        c1.metric("Total Spent (LKR)", f"{total_spent:,}")
        c2.metric("Total Orders Placed", total_orders)

        st.divider()

        st.caption("📅 Spending Timeline")
        if 'date' in df_hist.columns:
            spending_trend = df_hist.groupby('date')['price'].sum()
            st.line_chart(spending_trend, color="#00e676")

        st.caption("🛍️ Spending by Product")
        df_hist['clean_item'] = df_hist['item'].apply(
            lambda x: x.split(' (x')[0] if ' (x' in x else x)
        item_spend = df_hist.groupby('clean_item')['price'].sum()
        st.bar_chart(item_spend, color="#7c3aed")
    else:
        st.info("No purchase history found. Buy something to see stats!")

st.markdown("<br><br><center style='color:#666'>Dream Spells © 2025</center>",
            unsafe_allow_html=True)
