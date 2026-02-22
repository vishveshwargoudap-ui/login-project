from app import app,db

with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user' NOT NULL"))
        conn.execute(db.text("ALTER TABLE products ADD COLUMN IF NOT EXISTS seller_id INTEGER"))
        conn.execute(db.text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS  buyer_id INTEGER"))
        conn.commit()
        print("Database schema updated successfully.")
    

