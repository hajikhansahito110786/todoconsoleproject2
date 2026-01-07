import { NextRequest, NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error('DATABASE_URL is not set');
}
const sql = neon(connectionString!);

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> } // Add Promise type
) {
  try {
    // AWAIT params
    const { id } = await params;
    const classId = parseInt(id);
    
    const students = await sql`
      SELECT 
        sc.id as enrollment_id,
        sc.enrollment_date,
        sc.status,
        s.id,
        s.nameplz as student_name,
        s.email as student_email
      FROM studentclass sc
      JOIN student s ON sc.student_id = s.id
      WHERE sc.class_id = ${classId}
      ORDER BY sc.enrollment_date DESC
    `;
    
    return NextResponse.json({
      success: true,
      data: { students }
    });
  } catch (error: any) {
    console.error('Error fetching class students:', error);
    return NextResponse.json({
      success: true,
      data: { students: [] }
    });
  }
}