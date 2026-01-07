import { NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error('DATABASE_URL is not set');
  throw new Error('Database connection not configured');
}

const sql = neon(connectionString);

// Enroll student in class
export async function POST(request: Request) {
  try {
    const { studentId, className, classCode } = await request.json();
    
    console.log(`📝 Enrolling student ${studentId} in class ${className} (${classCode})`);
    
    if (!studentId || !className) {
      return NextResponse.json(
        { success: false, message: 'Student ID and Class Name are required' },
        { status: 400 }
      );
    }

    // Check if student exists
    const student = await sql`
      SELECT id, nameplz, email FROM student WHERE id = ${parseInt(studentId)}
    `;
    
    if (student.length === 0) {
      return NextResponse.json(
        { success: false, message: 'Student not found' },
        { status: 404 }
      );
    }

    // Check if class exists in classes table (optional validation)
    let classData = null;
    try {
      classData = await sql`
        SELECT id, class_name, instructor FROM classes 
        WHERE class_name = ${className} OR class_name ILIKE ${'%' + className + '%'}
        LIMIT 1
      `;
    } catch (error) {
      console.log('Classes table might not exist or have different structure');
    }

    // Check if already enrolled (using your studentclass table structure)
    const existing = await sql`
      SELECT 1 FROM studentclass 
      WHERE studentid = ${parseInt(studentId)} 
      AND class_name = ${className}
      ${classCode ? sql`AND class_code = ${classCode}` : sql``}
    `;
    
    if (existing.length > 0) {
      return NextResponse.json(
        { success: false, message: 'Student already enrolled in this class' },
        { status: 409 }
      );
    }

    // Create enrollment in studentclass table (with your fields)
    const enrollment = await sql`
      INSERT INTO studentclass (studentid, class_name, class_code) 
      VALUES (${parseInt(studentId)}, ${className}, ${classCode || null})
      RETURNING id, studentid, class_name, class_code
    `;
    
    console.log('✅ Enrollment created:', enrollment[0]);
    
    return NextResponse.json({
      success: true,
      message: `Enrolled ${student[0].nameplz} in ${className}`,
      data: {
        enrollment: enrollment[0],
        student: student[0],
        class: { className, classCode }
      }
    }, { status: 201 });
    
  } catch (error: any) {
    console.error('❌ Enrollment error:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to enroll: ' + error.message },
      { status: 500 }
    );
  }
}

// Get all enrollments
export async function GET() {
  try {
    const enrollments = await sql`
      SELECT 
        sc.id,
        sc.studentid,
        sc.class_name,
        sc.class_code,
        s.nameplz as student_name,
        s.email as student_email
      FROM studentclass sc
      LEFT JOIN student s ON sc.studentid = s.id
      ORDER BY sc.id DESC
    `;
    
    return NextResponse.json({
      success: true,
      data: {
        enrollments,
        count: enrollments.length
      }
    });
  } catch (error: any) {
    console.error('Error fetching enrollments:', error);
    return NextResponse.json({
      success: true,
      data: { enrollments: [], count: 0 }
    });
  }
}