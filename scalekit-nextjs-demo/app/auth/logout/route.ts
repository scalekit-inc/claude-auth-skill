import { NextRequest, NextResponse } from 'next/server';
import { scalekit, POST_LOGOUT_URL } from '@/lib/scalekit';
import { cookies } from 'next/headers';

export async function GET(request: NextRequest) {
  try {
    const cookieStore = await cookies();
    const idToken = cookieStore.get('idToken')?.value;

    console.log('Logout: idToken present:', !!idToken);
    console.log('Logout: POST_LOGOUT_URL:', POST_LOGOUT_URL);

    // Generate Scalekit logout URL
    // This logs out from Scalekit's session AND the identity provider
    const logoutUrl = scalekit.getLogoutUrl({
      idTokenHint: idToken,
      postLogoutRedirectUri: POST_LOGOUT_URL
    });

    console.log('Logout: Generated logout URL:', logoutUrl);

    // Create redirect response to Scalekit logout
    const response = NextResponse.redirect(logoutUrl);

    // Clear all auth cookies
    // Note: Use .set() with maxAge: 0 (not .delete()) for reliable cookie clearing
    const cookieOptions = { path: '/', maxAge: 0 };
    response.cookies.set('accessToken', '', cookieOptions);
    response.cookies.set('refreshToken', '', cookieOptions);
    response.cookies.set('idToken', '', cookieOptions);
    response.cookies.set('user', '', cookieOptions);

    console.log('User logged out - redirecting to Scalekit logout');

    return response;
  } catch (error) {
    console.error('Logout error - falling back to local logout:', error);
    console.error('Error details:', error instanceof Error ? error.message : String(error));

    // Fallback: Clear cookies and redirect to home even if Scalekit logout fails
    const response = NextResponse.redirect(new URL('/', request.url));
    const cookieOptions = { path: '/', maxAge: 0 };
    response.cookies.set('accessToken', '', cookieOptions);
    response.cookies.set('refreshToken', '', cookieOptions);
    response.cookies.set('idToken', '', cookieOptions);
    response.cookies.set('user', '', cookieOptions);

    return response;
  }
}
