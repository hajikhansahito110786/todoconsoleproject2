import { NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error('DATABASE_URL is not set');
}
const sql = neon(connectionString!);

// First, create the classes table if it doesn't exist
async function ensureClassesTable() {
  try {
    // Check if table exists
    await sql`
      SELECT 1 FROM classes LIMIT 1
    `;
  } catch (error: any) {
    // Create table if it doesn't exist
    if (error.message?.includes('relation "classes" does not exist')) {
      console.log('Creating classes table...');
      await sql`
        CREATE TABLE classes (
          id SERIAL PRIMARY KEY,
          class_name VARCHAR(255) NOT NULL,
          description TEXT,
          instructor VARCHAR(255) NOT NULL,
          max_students INTEGER,
          created_at TIMESTAMP DEFAULT NOW()
        )
      `;
      console.log('Classes table created');
    }
  }
}

export async function POST(request: Request) {
  try {
    await ensureClassesTable();
    
    const classData = await request.json();
    console.log('Creating class:', classData);
    
    // Validation
    if (!classData.className || !classData.instructor) {
      return NextResponse.json(
        { success: false, message: 'Class name and instructor are required' },
        { status: 400 }
      );
    }

    // Insert into classes table
    const result = await sql`
      INSERT INTO classes (class_name, description, instructor, max_students) 
      VALUES (${classData.className}, ${classData.description || null}, ${classData.instructor}, ${classData.maxStudents || null})
      RETURNING id, class_name as "className", description, instructor, max_students as "maxStudents", created_at
    `;
    
    const newClass = result[0];
    console.log('Class created with ID:', newClass.id);
    
    return NextResponse.json({
      success: true,
      message: 'Class created successfully',
      class: newClass
    }, { status: 201 });
    
  } catch (error: any) {
    console.error('Error creating class:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to create class: ' + error.message },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    await ensureClassesTable();
    
    const classes = await sql`
      SELECT id, class_name as "className", description, instructor, max_students as "maxStudents", created_at 
      FROM classes 
      ORDER BY created_at DESC
    `;
    
    return NextResponse.json({
      success: true,
      data: {
        classes,
        count: classes.length
      }
    });
  } catch (error: any) {
    console.error('Error fetching classes:', error);
    return NextResponse.json({
      success: true,
      data: { classes: [], count: 0 }
    });
  }
}