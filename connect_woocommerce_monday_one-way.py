import requests

# =====================================================
# CONFIGURATION
# =====================================================
import os
import requests
from datetime import datetime

print(f"Sync started at {datetime.now()}")

# ---------- Monday ----------
MONDAY_API_KEY = os.environ["MONDAY_API_KEY"]
BOARD_ID = int(os.environ["MONDAY_BOARD_ID"])

COLUMN_WC_ID = "text_mm4d2hcf"
COLUMN_WC_STOCK = "numeric_mm4dxf34"

# ---------- WooCommerce ----------
# Change this if your API endpoint is different.
WC_API_URL = os.environ["SITE_URL"]

WC_CONSUMER_KEY = os.environ["WC_CONSUMER_KEY"]
WC_CONSUMER_SECRET = os.environ["WC_CONSUMER_SECRET"]

MONDAY_URL = "https://api.monday.com/v2"

HEADERS = {
    "Authorization": MONDAY_API_KEY,
    "Content-Type": "application/json"
}

# =====================================================
# GET ALL ITEMS FROM THE BOARD
# =====================================================

query = f"""
query {{
  boards(ids: {BOARD_ID}) {{
    items_page(limit: 500) {{
      items {{
        id
        name
        column_values(ids: [
          "{COLUMN_WC_ID}"
        ]) {{
          id
          text
        }}
      }}
    }}
  }}
}}
"""

response = requests.post(
    MONDAY_URL,
    json={"query": query},
    headers=HEADERS
)

response.raise_for_status()

result = response.json()

items = result["data"]["boards"][0]["items_page"]["items"]

print(f"Found {len(items)} item(s) on the board.")

# =====================================================
# PROCESS EACH ITEM
# =====================================================

for item in items:

    item_id = item["id"]
    item_name = item["name"]

    values = {
        col["id"]: col["text"]
        for col in item["column_values"]
    }

    wc_product_id = values.get(COLUMN_WC_ID, "").strip()

    if wc_product_id == "":
        print(f"Skipping '{item_name}' (no WooCommerce ID)")
        continue

    try:
        # ---------------------------------------------
        # GET PRODUCT FROM WOOCOMMERCE
        # ---------------------------------------------

        wc_response = requests.get(
            f"{WC_API_URL}/products/{wc_product_id}",
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET)
        )

        wc_response.raise_for_status()

        product = wc_response.json()

        stock_quantity = product.get("stock_quantity")

        if stock_quantity is None:
            stock_quantity = 0

        print(
            f"'{item_name}' "
            f"(WooCommerce ID {wc_product_id}) "
            f"-> stock = {stock_quantity}"
        )

        # ---------------------------------------------
        # UPDATE MONDAY COLUMN
        # ---------------------------------------------

        mutation = f"""
        mutation {{
          change_simple_column_value(
            board_id: {BOARD_ID},
            item_id: {item_id},
            column_id: "{COLUMN_WC_STOCK}",
            value: "{stock_quantity}"
          ) {{
            id
          }}
        }}
        """

        update = requests.post(
            MONDAY_URL,
            json={"query": mutation},
            headers=HEADERS
        )

        update.raise_for_status()

        print("   Monday updated successfully.")

    except Exception as e:
        print(f"ERROR processing '{item_name}': {e}")

print("\nFinished.")
