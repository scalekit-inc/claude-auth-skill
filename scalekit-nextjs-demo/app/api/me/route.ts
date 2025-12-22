import { NextRequest, NextResponse } from 'next/server';
import { requireAuth } from '@/lib/auth';
import { cookies } from 'next/headers';

export async function GET(request: NextRequest) {
  try {
    const claims = await requireAuth();
    const cookieStore = await cookies();
    const userCookie = cookieStore.get('user')?.value;

    const user = userCookie ? JSON.parse(userCookie) : null;

    return NextResponse.json({
      user,
      claims,
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Not authenticated' },
      { status: 401 }
    );
  }
}
