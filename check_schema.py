# check_schema.py
from sqlmodel import create_engine, text
from sqlalchemy import inspect

DATABASE_URL = "postgresql://neondb_owner:npg_rcbta9i6JCwR@ep-broad-field-adscc1ik-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)

# Check what tables exist
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Existing tables: {tables}")

# Check student table columns
if 'student' in tables:
    columns = inspector.get_columns('student')
    print("\nStudent table columns:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")

# Check studentclasses table (if it exists)
if 'studentclasses' in tables:
    columns = inspector.get_columns('studentclasses')
    print("\nStudentClasses table columns:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
else:
    print("\nStudentClasses table doesn't exist yet")