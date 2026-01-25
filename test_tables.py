# test_tables.py
import os
from dotenv import load_dotenv
from sqlmodel import create_engine, text, Session

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)

with Session(engine) as session:
    # Check todo table columns
    print("📊 TODO TABLE COLUMNS:")
    result = session.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'todo' 
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  - {row[0]}: {row[1]}")
    
    print("\n📊 STUDENT TABLE COLUMNS:")
    result = session.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'student' 
        ORDER BY ordinal_position
    """))
    for row in result:
        print(f"  - {row[0]}: {row[1]}")