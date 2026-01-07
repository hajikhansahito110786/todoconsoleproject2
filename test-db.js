const { neon } = require('@neondatabase/serverless');

async function testConnection() {
  const sql = neon(process.env.DATABASE_URL);
  
  try {
    const result = await sql`SELECT NOW() as current_time`;
    console.log('✅ Database connection successful:', result[0]);
    
    // Test table exists
    const tables = await sql`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public'
    `;
    console.log('📊 Tables in database:', tables);
    
  } catch (error) {
    console.error('❌ Connection failed:', error.message);
  }
}

testConnection();