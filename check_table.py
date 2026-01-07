# check_table.py
from sqlmodel import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)

inspector = inspect(engine)

# Check student table columns
print("📊 Student Table Columns:")
columns = inspector.get_columns('student')
for column in columns:
    print(f"  - {column['name']}: {column['type']}")

# Check if name field exists
has_nameplz = any(col['name'] == 'nameplz' for col in columns)
has_name = any(col['name'] == 'name' for col in columns)

print(f"\n✅ Has 'nameplz' field: {has_nameplz}")
print(f"✅ Has 'name' field: {has_name}")