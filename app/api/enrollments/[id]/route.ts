import { NextRequest, NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error('DATABASE_URL is not set');
  throw new Error('Database connection not configured');
}

const sql = neon(connectionString);

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> } // Add Promise type
) {
  try {
    // AWAIT params first
    const { id } = await params;
    const enrollmentId = parseInt(id);
    
    console.log(`🗑️ Removing enrollment ID: ${enrollmentId}`);
    
    if (isNaN(enrollmentId)) {
      return NextResponse.json(
        { success: false, message: 'Invalid enrollment ID' },
        { status: 400 }
      );
    }

    // Get enrollment details before deleting
    const enrollment = await sql`
      SELECT sc.*, s.nameplz 
      FROM studentclass sc
      LEFT JOIN student s ON sc.studentid = s.id
      WHERE sc.id = ${enrollmentId}
    `;
    
    if (enrollment.length === 0) {
      return NextResponse.json(
        { success: false, message: 'Enrollment not found' },
        { status: 404 }
      );
    }

    // Delete from studentclass table
    const result = await sql`
      DELETE FROM studentclass 
      WHERE id = ${enrollmentId}
      RETURNING id, studentid, class_name
    `;
    
    console.log('✅ Enrollment removed:', result[0]);
    
    return NextResponse.json({
      success: true,
      message: `Removed ${enrollment[0].nameplz} from ${enrollment[0].class_name}`
    });
    
  } catch (error: any) {
    console.error('❌ Error removing enrollment:', error);
    return NextResponse.json(
      { success: false, message: 'Failed to remove enrollment: ' + error.message },
      { status: 500 }
    );
  }
}