# add_missing_columns_fixed.py
import os
from dotenv import load_dotenv
from sqlmodel import create_engine, text, Session

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if "neon.tech" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL, echo=False)  # Disable echo for cleaner output

print("🔄 ADDING MISSING COLUMNS TO EXISTING TABLES...")
print("=" * 60)

def add_column_if_not_exists(session, table, column, column_type):
    """Safely add a column if it doesn't exist"""
    try:
        # Check if column exists
        result = session.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{column}'
            )
        """))
        column_exists = result.scalar()
        
        if not column_exists:
            print(f"   Adding column: {column} ({column_type})")
            session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"))
            print(f"   ✅ Added {column}")
            return True
        else:
            print(f"   ✅ Column {column} already exists")
            return False
    except Exception as e:
        print(f"   ⚠️ Error checking/adding {column}: {e}")
        return False

def rename_column_if_exists(session, table, old_name, new_name):
    """Rename a column if old_name exists and new_name doesn't"""
    try:
        # Check if old column exists
        result = session.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{old_name}'
            )
        """))
        old_exists = result.scalar()
        
        # Check if new column exists
        result = session.execute(text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{new_name}'
            )
        """))
        new_exists = result.scalar()
        
        if old_exists and not new_exists:
            print(f"   Renaming {old_name} to {new_name}...")
            session.execute(text(f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}"))
            print(f"   ✅ Renamed {old_name} to {new_name}")
            return True
        elif new_exists:
            print(f"   ✅ Column {new_name} already exists (keeping both)")
            return False
        else:
            print(f"   ℹ️ Column {old_name} doesn't exist, nothing to rename")
            return False
    except Exception as e:
        print(f"   ⚠️ Error renaming {old_name} to {new_name}: {e}")
        return False

with Session(engine) as session:
    try:
        # 1. Check STUDENT table
        print("\n1. Checking STUDENT table...")
        
        # Add missing columns to student table
        student_columns = [
            ("name", "VARCHAR(255)"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("created_by", "VARCHAR(255)"),
            ("updated_by", "VARCHAR(255)"),
            ("last_ip_address", "VARCHAR(50)"),
            ("last_user_agent", "TEXT")
        ]
        
        for col_name, col_type in student_columns:
            add_column_if_not_exists(session, "student", col_name, col_type)
        
        # If we just added 'name' column and 'nameplz' exists, copy data
        try:
            result = session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'student' AND column_name = 'nameplz'
                )
            """))
            nameplz_exists = result.scalar()
            
            result = session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'student' AND column_name = 'name'
                )
            """))
            name_exists = result.scalar()
            
            if nameplz_exists and name_exists:
                # Check if name column is empty
                result = session.execute(text("SELECT COUNT(*) FROM student WHERE name IS NULL"))
                null_names = result.scalar()
                
                if null_names > 0:
                    print(f"   Copying data from nameplz to name for {null_names} records...")
                    session.execute(text("UPDATE student SET name = nameplz WHERE name IS NULL"))
                    print("   ✅ Data copied")
        except Exception as e:
            print(f"   ⚠️ Error copying name data: {e}")
        
        session.commit()  # Commit student changes
        
        # 2. Check TODO table
        print("\n2. Checking TODO table...")
        
        # Rename columns first
        column_renames = [
            ("userwhofeeded", "created_by"),
            ("last_updated_by", "updated_by"),
            ("last_updated_at", "updated_at")
        ]
        
        for old_name, new_name in column_renames:
            rename_column_if_exists(session, "todo", old_name, new_name)
        
        session.commit()  # Commit rename changes
        
        # Add missing columns to todo table
        todo_columns = [
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("created_by", "VARCHAR(255)"),
            ("updated_by", "VARCHAR(255)"),
            ("last_ip_address", "VARCHAR(50)"),
            ("last_user_agent", "TEXT")
        ]
        
        for col_name, col_type in todo_columns:
            add_column_if_not_exists(session, "todo", col_name, col_type)
        
        session.commit()  # Commit todo changes
        
        # 3. Create audit_log table if it doesn't exist
        print("\n3. Checking AUDIT_LOG table...")
        
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'audit_log'
            )
        """))
        audit_log_exists = result.scalar()
        
        if not audit_log_exists:
            print("   Creating audit_log table...")
            session.execute(text("""
                CREATE TABLE audit_log (
                    id SERIAL PRIMARY KEY,
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(100) NOT NULL,
                    resource_id INTEGER,
                    details TEXT,
                    user_id VARCHAR(100),
                    ip_address VARCHAR(50),
                    user_agent TEXT,
                    computer_name VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("   ✅ Created audit_log table")
        else:
            print("   ✅ audit_log table already exists")
        
        session.commit()
        
        # 4. Verify the final structure
        print("\n" + "=" * 60)
        print("📊 FINAL TABLE STRUCTURES:")
        print("=" * 60)
        
        for table in ['student', 'todo', 'audit_log']:
            print(f"\n{table.upper()} table:")
            result = session.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            if columns:
                for row in columns:
                    print(f"  - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
            else:
                print(f"  Table doesn't exist or has no columns")
        
        # Show data counts
        print("\n" + "=" * 60)
        print("📊 DATA COUNTS:")
        print("=" * 60)
        
        student_count = session.execute(text("SELECT COUNT(*) FROM student")).scalar()
        todo_count = session.execute(text("SELECT COUNT(*) FROM todo")).scalar()
        
        print(f"Students: {student_count}")
        print(f"Todos: {todo_count}")
        
        # Show column mappings
        print("\n" + "=" * 60)
        print("🔗 COLUMN MAPPINGS (for your code):")
        print("=" * 60)
        print("Your code should now use these column names:")
        print("\nSTUDENT table:")
        print("  - id, name, email, created_at, updated_at,")
        print("    created_by, updated_by, last_ip_address, last_user_agent")
        print("  - Note: 'nameplz' column is still preserved for other projects")
        
        print("\nTODO table:")
        print("  - id, title, description, priority, status, due_date,")
        print("    student_id, created_at, completed_at, updated_at,")
        print("    created_by, updated_by, last_ip_address, last_user_agent")
        
        print("\n" + "=" * 60)
        print("🎉 Database upgrade complete! Both old and new projects will work.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()