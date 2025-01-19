import streamlit as st
import json
import os
from collections import defaultdict
import time

# ------------------------------------------------
# 1. Utility functions to load/save dishes in JSON
# ------------------------------------------------
def load_dishes(json_path):
    if not os.path.exists(json_path):
        return {}
    with open(json_path, "r") as f:
        return json.load(f)

def save_dishes(dishes_db, json_path):
    with open(json_path, "w") as f:
        json.dump(dishes_db, f, indent=4)

# ------------------------------------------------
# 2. Streamlit page config (use wide layout)
# ------------------------------------------------
st.set_page_config(layout="wide")

# ------------------------------------------------
# 3. Inject custom CSS for a table-like grid
# ------------------------------------------------
st.markdown(
    """
    <style>
    .table-grid {
      display: table;
      border-collapse: collapse;
      width: 100%;
      margin-bottom: 1rem;
    }
    .table-grid-row {
      display: table-row;
    }
    .table-grid-cell {
      display: table-cell;
      border: 1px solid #ccc;
      padding: 8px;
      vertical-align: top;  /* keep content top-aligned */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------
# 4. Load data into session state
# ------------------------------------------------
JSON_PATH = "dishes.json"

if "dishes_db" not in st.session_state:
    st.session_state["dishes_db"] = load_dishes(JSON_PATH)
dishes_db = st.session_state["dishes_db"]

if "meal_plan" not in st.session_state:
    st.session_state["meal_plan"] = defaultdict(lambda: defaultdict(list))
meal_plan = st.session_state["meal_plan"]

# Keep a separate list in session_state for stand-alone misc items
if "misc_items" not in st.session_state:
    st.session_state["misc_items"] = []

# Keep track of last button click time to throttle repeated clicks
if "last_click_time" not in st.session_state:
    st.session_state["last_click_time"] = 0

# ------------------------------------------------
# 5. Basic config
# ------------------------------------------------
meal_types = ["Breakfast", "Lunch", "Dinner"]
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.title("Mesamie's Weekly Rations")

# ------------------------------------------------
# 6. Create two tabs
# ------------------------------------------------
tab_meal_plan, tab_add_dish = st.tabs(["Meal Plan", "Add a New Dish"])

# ------------------------------------------------
# 7. TAB 1: Meal Plan Calendar
# ------------------------------------------------
with tab_meal_plan:
    st.subheader("Weekly Calendar")

    # ----------------------------------
    # 7.1: Left Sidebar Controls
    # ----------------------------------
    st.sidebar.title("Add Meals and Items")

    # A) "Add or Clean a Cell"
    st.sidebar.header("Add or Clean a Cell")
    selected_day = st.sidebar.selectbox("Select Day", days_of_week)
    selected_meal = st.sidebar.selectbox("Select Meal", meal_types)

    # Insert a special option for "CLEAN THE CELL"
    dish_options = ["CLEAN THE CELL"] + sorted(list(dishes_db.keys()))
    selected_dish = st.sidebar.selectbox("Select Dish", dish_options)

    # Throttled "Confirm Selection" button
    if st.sidebar.button("Confirm Selection"):
        current_time = time.time()
        if current_time - st.session_state["last_click_time"] > 1:  # 1-second delay
            if selected_dish == "CLEAN THE CELL":
                # Remove all dishes in that cell
                meal_plan[selected_day][selected_meal] = []
                st.sidebar.success(f"Cleared {selected_day} ({selected_meal}).")
            else:
                meal_plan[selected_day][selected_meal].append(selected_dish)
                st.sidebar.success(f"Added '{selected_dish}' to {selected_day} ({selected_meal}).")

            # Update the last click time and rerun
            st.session_state["last_click_time"] = current_time
            st.experimental_rerun()
        else:
            st.sidebar.warning("Please wait before clicking again.")

    # B) "Clear All" button (for the entire meal plan)
    st.sidebar.header("Clear Everything")
    if st.sidebar.button("Clear All"):
        current_time = time.time()
        if current_time - st.session_state["last_click_time"] > 1:  # 1-second delay
            st.session_state["meal_plan"] = defaultdict(lambda: defaultdict(list))
            st.sidebar.success("Cleared the entire meal plan.")

            st.session_state["last_click_time"] = current_time
            st.experimental_rerun()
        else:
            st.sidebar.warning("Please wait before clicking again.")

    # ----------------------------------
    # 7.2: Misc Items Section on Sidebar
    # ----------------------------------
    st.sidebar.header("Additional Items (Not Tied to Calendar)")

    misc_item_name = st.sidebar.text_input("Misc Item Name (e.g. 'Loaf of bread')")

    # Example unit dropdown
    misc_unit_choices = ["", "g", "lb", "oz", "piece", "head", "ml", "cup"]
    misc_selected_unit = st.sidebar.selectbox("Unit (Optional)", misc_unit_choices)

    # Decide increment step based on the selected unit
    step_value = 1.0
    if misc_selected_unit == "g":
        step_value = 100.0
    elif misc_selected_unit == "lb":
        step_value = 0.5
    elif misc_selected_unit == "ml":
        step_value = 50.0
    # etc. if needed

    misc_quantity = st.sidebar.number_input("Quantity (Optional)", step=step_value, value=0.0)

    # Throttled "Add Misc Item" button
    if st.sidebar.button("Add Misc Item"):
        current_time = time.time()
        if current_time - st.session_state["last_click_time"] > 1:  # 1-second delay
            if not misc_item_name.strip():
                st.sidebar.warning("Please provide at least a name for the item.")
            else:
                st.session_state["misc_items"].append({
                    "name": misc_item_name,
                    "unit": misc_selected_unit,
                    "quantity": misc_quantity
                })
                st.sidebar.success(f"Added '{misc_item_name}' to Misc Items.")
                st.session_state["last_click_time"] = current_time
                st.experimental_rerun()
        else:
            st.sidebar.warning("Please wait before clicking again.")

    st.sidebar.write("### Current Misc Items")
    if not st.session_state["misc_items"]:
        st.sidebar.write("No extra items yet.")
    else:
        # For each item, let the user remove it (also throttled)
        for i, item in enumerate(st.session_state["misc_items"]):
            col1, col2, col3, col4 = st.sidebar.columns([2, 1, 1, 1])
            with col1:
                st.write(item["name"])
            with col2:
                st.write(item["unit"] if item["unit"] else "-")
            with col3:
                st.write(item["quantity"] if item["quantity"] else "-")
            with col4:
                # Throttle individual remove button
                if st.button("Remove", key=f"remove_misc_{i}"):
                    current_time = time.time()
                    if current_time - st.session_state["last_click_time"] > 1:  # 1-second delay
                        st.session_state["misc_items"].pop(i)
                        st.session_state["last_click_time"] = current_time
                        st.experimental_rerun()
                    else:
                        st.warning("Please wait before clicking again.")

    # ----------------------------------
    # 7.3: Calendar Table (HTML-based)
    # ----------------------------------
    table_html = "<div class='table-grid'>"

    # Header row
    table_html += "<div class='table-grid-row'>"
    table_html += "<div class='table-grid-cell'><strong>Meal Type</strong></div>"
    for day in days_of_week:
        table_html += f"<div class='table-grid-cell'><strong>{day}</strong></div>"
    table_html += "</div>"  # end header row

    # Rows for each meal type
    for meal_type in meal_types:
        table_html += "<div class='table-grid-row'>"
        # First cell: meal type label
        table_html += f"<div class='table-grid-cell'><strong>{meal_type}</strong></div>"

        # Cells for each day
        for day in days_of_week:
            dishes = meal_plan[day][meal_type]  # list of dish names
            cell_content = ", ".join(dishes) if dishes else "-"
            table_html += f"<div class='table-grid-cell'>{cell_content}</div>"

        table_html += "</div>"  # end row

    table_html += "</div>"  # end .table-grid

    st.markdown(table_html, unsafe_allow_html=True)

    # ----------------------------------
    # 7.4: Shopping List
    # ----------------------------------
    st.subheader("Shopping List")

    shopping_list = defaultdict(lambda: defaultdict(float))

    # Aggregate items from the Meal Plan
    for day, meals in meal_plan.items():
        for mtype, dish_list in meals.items():
            for dish_name in dish_list:
                if dish_name not in dishes_db:
                    # If somehow a dish is missing from the DB, skip
                    continue
                for ingr in dishes_db[dish_name]["ingredients"]:
                    cat = ingr["category"]
                    name = ingr["name"]
                    shopping_list[cat][name] += ingr["quantity"]

    # Add Misc Items under category "Misc" 
    for item in st.session_state["misc_items"]:
        cat = "Misc"
        name = item["name"]
        qty = item["quantity"]
        shopping_list[cat][name] += qty

    # Display final aggregated list
    if not shopping_list:
        st.write("No items in the shopping list yet.")
    else:
        for category, items in shopping_list.items():
            st.write(f"### {category}")
            for item_name, total_qty in items.items():
                # We skip unit logic here for clarity, or you can add as needed
                st.write(f"- {item_name}: {total_qty}")

# ------------------------------------------------
# 8. TAB 2: Add a New Dish
# ------------------------------------------------
with tab_add_dish:
    st.subheader("Create a New Dish (Saved to JSON)")

    new_dish_name = st.text_input("Dish Name", value="")

    # We'll store new dish's ingredients in session_state
    if "new_dish_ingredients" not in st.session_state:
        st.session_state["new_dish_ingredients"] = []

    # Button to add a new blank ingredient row
    if st.button("Add Ingredient Row"):
        st.session_state["new_dish_ingredients"].append(
            {"name": "", "quantity": 0.0, "unit": "", "category": ""}
        )

    category_options = ["Produce", "Meat", "Dairy", "Dry Goods", "Canned Goods", "Bakery", "Other"]
    unit_choices = ["g", "lb", "oz", "piece", "head", "ml", "cup", ""]

    for idx, ingredient in enumerate(st.session_state["new_dish_ingredients"]):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

        # 1. Name
        with c1:
            st.session_state["new_dish_ingredients"][idx]["name"] = st.text_input(
                f"Name {idx+1}",
                value=ingredient["name"],
                key=f"name_{idx}"
            )

        # 2. Unit (selectbox first)
        with c2:
            if ingredient["unit"] in unit_choices:
                unit_index = unit_choices.index(ingredient["unit"])
            else:
                unit_index = 0
            selected_unit = st.selectbox(
                f"Unit {idx+1}",
                unit_choices,
                index=unit_index,
                key=f"unit_{idx}"
            )
            st.session_state["new_dish_ingredients"][idx]["unit"] = selected_unit

        # 3. Quantity (with dynamic step)
        step_value = 1.0
        if selected_unit == "g":
            step_value = 100.0
        elif selected_unit == "lb":
            step_value = 0.5
        elif selected_unit == "oz":
            step_value = 1.0
        elif selected_unit == "ml":
            step_value = 50.0
        # etc.

        st.session_state["new_dish_ingredients"][idx]["quantity"] = st.number_input(
            f"Qty {idx+1}",
            value=float(ingredient["quantity"]),
            step=step_value,
            key=f"qty_{idx}"
        )

        # 4. Category (dropdown)
        with c4:
            if ingredient["category"] in category_options:
                cat_index = category_options.index(ingredient["category"])
            else:
                cat_index = 0
            st.session_state["new_dish_ingredients"][idx]["category"] = st.selectbox(
                f"Category {idx+1}",
                category_options,
                index=cat_index,
                key=f"cat_{idx}"
            )

    # Button to save the new dish
    if st.button("Save New Dish"):
        if not new_dish_name.strip():
            st.error("Please provide a valid dish name.")
        else:
            # Construct the new dish object
            new_dish_data = {
                "ingredients": st.session_state["new_dish_ingredients"]
            }
            # Update the in-memory DB
            dishes_db[new_dish_name] = new_dish_data

            # Persist to JSON
            save_dishes(dishes_db, JSON_PATH)
            st.success(f"New dish '{new_dish_name}' has been added to the database!")

            # Clear the form
            st.session_state["new_dish_ingredients"] = []
            st.experimental_rerun()
