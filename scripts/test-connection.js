import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Load .env file
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, '..', '.env') });

const connectionString = process.env.DATABASE_URL;

async function testConnection() {
  if (!connectionString) {
    console.error('❌ DATABASE_URL is not set in .env file');
    return;
  }
  
  console.log('🔗 Testing connection to Neon database...');
  
  const sql = neon(connectionString);
  
  try {
    // Test basic connection
    const result = await sql`SELECT NOW() as current_time, version() as postgres_version`;
    console.log('✅ Connection successful!');
    console.log('📅 Current time:', result[0].current_time);
    console.log('🐘 PostgreSQL version:', result[0].postgres_version);
    
    // Check if students table exists
    try {
      const tables = await sql`
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'students'
      `;
      
      if (tables.length > 0) {
        console.log('✅ Students table exists');
        
        // Count records
        const countResult = await sql`SELECT COUNT(*) as count FROM students`;
        console.log(`📊 Records in students table: ${countResult[0].count}`);
      } else {
        console.log('⚠️  Students table does not exist');
        console.log('💡 Run this SQL in Neon Console:');
        console.log(`
          CREATE TABLE students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            age INTEGER,
            grade VARCHAR(50),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
          )
        `);
      }
    } catch (tableError) {
      console.log('⚠️  Students table does not exist');
    }
    
  } catch (error) {
    console.error('❌ Connection failed:', error.message);
    console.log('💡 Check your DATABASE_URL in .env file');
  }
}

testConnection();