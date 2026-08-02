

def fetch_user_query():
    return "SELECT id, email, account_type, created_at FROM users WHERE id = %s;"

def fetch_user_inventory_all():
    return "SELECT user_id, product_id, products.p_name, quantity, inserted_at FROM item_levels, products WHERE user_id = %s AND products.id = product_id;"

def fetch_user_inventory_latest():
    return """SELECT
        user_id,
        product_id,
        products.p_name,
        quantity,
        inserted_at
    FROM (
        SELECT
            user_id,
            product_id,
            quantity,
            inserted_at,
            ROW_NUMBER() OVER(PARTITION BY product_id ORDER BY inserted_at DESC) as row_num
        FROM item_levels
        WHERE user_id = %s
    ) as ranked_items, products
    WHERE row_num = 1 AND products.id = product_id;"""
