import { NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error('❌ DATABASE_URL is not set');
}
const sql = neon(connectionString!);

export async function POST(request: Request) {
  try {
    const studentData = await request.json();
    console.log('📝 Creating student in "student" table:', studentData);
    
    // Basic validation
    if (!studentData.name || !studentData.email) {
      return NextResponse.json(
        { success: false, message: 'Name and email are required' },
        { status: 400 }
      );
    }

    // Insert into "student" table (uses nameplz column for name)
    const result = await sql`
      INSERT INTO student (nameplz, email) 
      VALUES (${studentData.name}, ${studentData.email})
      RETURNING id, nameplz as name, email, created_at
    `;
    
    const newStudent = result[0];
    console.log('✅ Student saved to "student" table, ID:', newStudent.id);
    
    return NextResponse.json({
      success: true,
      message: 'Student created successfully',
      student: newStudent
    }, { status: 201 });
    
  } catch (error: any) {
    console.error('❌ Database error:', error.message);
    
    // Handle duplicate email
    if (error.code === '23505' || error.message?.includes('duplicate')) {
      return NextResponse.json(
        { success: false, message: 'Email already exists' },
        { status: 409 }
      );
    }
    
    // Handle missing table
    if (error.message?.includes('relation "student" does not exist')) {
      return NextResponse.json(
        { 
          success: false, 
          message: 'Student table not found. Please check your database.' 
        },
        { status: 500 }
      );
    }
    
    return NextResponse.json(
      { success: false, message: 'Database error: ' + error.message },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    console.log('📋 Fetching from "student" table...');
    // Use nameplz as name in response
    const allStudents = await sql`
      SELECT id, nameplz as name, email, created_at 
      FROM student 
      ORDER BY created_at DESC
    `;
    
    console.log(`✅ Found ${allStudents.length} students`);
    
    return NextResponse.json({
      success: true,
      data: {
        students: allStudents,
        count: allStudents.length
      }
    });
  } catch (error: any) {
    console.error('GET Error:', error.message);
    
    // If table doesn't exist, return empty
    if (error.message?.includes('relation "student" does not exist')) {
      return NextResponse.json({
        success: true,
        data: { students: [], count: 0 }
      });
    }
    
    return NextResponse.json({
      success: false,
      message: 'Failed to fetch students: ' + error.message
    }, { status: 500 });
  }
}