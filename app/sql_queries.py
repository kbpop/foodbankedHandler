

def fetch_user_query(user_id):
    return f"SELECT id, username, created_at FROM users WHERE id = {user_id};"

def fetch_user_inventory_all(user_id):
    return f"SELECT user_id, product_id, products.p_name, quantity, inserted_at FROM item_levels, products WHERE user_id = {user_id} AND products.id = product_id;"

def fetch_user_inventory_latest(user_id):
    return f"""SELECT 
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
        WHERE user_id = {user_id}
    ) as ranked_items, products
    WHERE row_num = 1 AND products.id = product_id;"""
