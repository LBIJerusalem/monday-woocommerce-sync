import requests

# =====================================================
# CONFIGURATION
# =====================================================

# ---------- Monday ----------
MONDAY_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUwNjAxMjczOSwiYWFpIjoxMSwidWlkIjo0MDUyODE5MSwiaWFkIjoiMjAyNS0wNC0yOVQxMTo1NzowNy4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTU3MzYzODksInJnbiI6ImV1YzEifQ.F3z0qyToAiKMuyhIUGanWk0gSLt3agxM876oYcdTWzg"
BOARD_ID = 5098735316

COLUMN_WC_ID = "text_mm4d2hcf"
COLUMN_WC_STOCK = "numeric_mm4dxf34"

# ---------- WooCommerce ----------
# Change this if your API endpoint is different.
WC_API_URL = "https://leobaeck.org/wp-json/wc/v3"

WC_CONSUMER_KEY = "ck_a1ecc6646ac3d593a2be660191673044aea66671"
WC_CONSUMER_SECRET = "cs_8a0090fcd59e0ea6b06e1f82715eae0dc01e40fb"

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
