import { connect } from '@sqlmodel/core';
import { Student } from './models/Student';

// Get your Neon database URL from environment variables
const DATABASE_URL = process.env.DATABASE_URL || 'your_neon_connection_string_here';

export async function connectDB() {
  try {
    await connect(DATABASE_URL);
    console.log('✅ Connected to Neon database');
    
    // Sync models (create tables if they don't exist)
    await Student.sync();
    console.log('✅ Student table synchronized');
  } catch (error) {
    console.error('❌ Database connection failed:', error);
    throw error;
  }
}