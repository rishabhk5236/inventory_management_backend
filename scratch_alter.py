import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL"))
    conn.commit()
print("Added order_date column to orders table")
