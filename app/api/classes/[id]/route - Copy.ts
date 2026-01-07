import { NextRequest, NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error('DATABASE_URL is not set');
}
const sql = neon(connectionString!);

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const classId = params.id;
    
    const result = await sql`
      SELECT 
        id, 
        class_name as "className", 
        description, 
        instructor, 
        max_students as "maxStudents", 
        created_at
      FROM classes 
      WHERE id = ${parseInt(classId)}
    `;
    
    if (result.length === 0) {
      return NextResponse.json(
        { success: false, message: 'Class not found' },
        { status: 404 }
      );
    }
    
    return NextResponse.json({
      success: true,
      data: result[0]
    });
    
  } catch (error: any) {
    console.error('Error fetching class:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to fetch class: ' + error.message },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const classId = params.id;
    const classData = await request.json();
    
    // Validation
    if (!classData.className || !classData.instructor) {
      return NextResponse.json(
        { success: false, message: 'Class name and instructor are required' },
        { status: 400 }
      );
    }

    const result = await sql`
      UPDATE classes 
      SET 
        class_name = ${classData.className},
        description = ${classData.description || null},
        instructor = ${classData.instructor},
        max_students = ${classData.maxStudents || null}
      WHERE id = ${parseInt(classId)}
      RETURNING id, class_name as "className", description, instructor, max_students as "maxStudents", created_at
    `;
    
    if (result.length === 0) {
      return NextResponse.json(
        { success: false, message: 'Class not found' },
        { status: 404 }
      );
    }
    
    return NextResponse.json({
      success: true,
      message: 'Class updated successfully',
      data: result[0]
    });
    
  } catch (error: any) {
    console.error('Error updating class:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to update class: ' + error.message },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const classId = params.id;
    
    const result = await sql`
      DELETE FROM classes 
      WHERE id = ${parseInt(classId)}
      RETURNING id
    `;
    
    if (result.length === 0) {
      return NextResponse.json(
        { success: false, message: 'Class not found' },
        { status: 404 }
      );
    }
    
    return NextResponse.json({
      success: true,
      message: 'Class deleted successfully'
    });
    
  } catch (error: any) {
    console.error('Error deleting class:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to delete class: ' + error.message },
      { status: 500 }
    );
  }
}