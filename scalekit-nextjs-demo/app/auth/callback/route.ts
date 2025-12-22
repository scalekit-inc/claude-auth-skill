import { NextRequest, NextResponse } from 'next/server';
import { scalekit, CALLBACK_URL, cookieConfig } from '@/lib/scalekit';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get('code');
  const error = searchParams.get('error');
  const errorDescription = searchParams.get('error_description');

  // Handle OAuth errors
  if (error) {
    console.error('OAuth error:', error, errorDescription);
    return NextResponse.redirect(
      new URL(`/?error=${encodeURIComponent(errorDescription || error)}`, request.url)
    );
  }

  if (!code) {
    return new Response('Authorization code missing', { status: 400 });
  }

  try {
    // Exchange code for tokens
    const result = await scalekit.authenticateWithCode(code, CALLBACK_URL);

    const { accessToken, refreshToken, idToken, user, expiresIn } = result;

    // Create redirect response
    const response = NextResponse.redirect(new URL('/dashboard', request.url));

    // Set cookies
    response.cookies.set('accessToken', accessToken, {
      ...cookieConfig,
      maxAge: expiresIn,
    });

    response.cookies.set('refreshToken', refreshToken, {
      ...cookieConfig,
      maxAge: 30 * 24 * 60 * 60, // 30 days
    });

    response.cookies.set('idToken', idToken, {
      ...cookieConfig,
      maxAge: expiresIn,
    });

    // Store user info (not httpOnly so frontend can access)
    response.cookies.set('user', JSON.stringify(user), {
      maxAge: expiresIn,
      secure: cookieConfig.secure,
      sameSite: cookieConfig.sameSite,
      path: '/',
    });

    console.log('User authenticated:', user.email);

    return response;
  } catch (error) {
    console.error('Authentication error:', error);
    return NextResponse.redirect(
      new URL('/?error=Authentication%20failed', request.url)
    );
  }
}
