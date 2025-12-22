import { NextRequest } from 'next/server';
import { scalekit, CALLBACK_URL } from '@/lib/scalekit';

export async function GET(request: NextRequest) {
  try {
    const authorizationUrl = scalekit.getAuthorizationUrl(CALLBACK_URL, {
      scopes: ['openid', 'profile', 'email', 'offline_access'],
    });

    return Response.redirect(authorizationUrl);
  } catch (error) {
    console.error('Login error:', error);
    return new Response('Failed to initiate login', { status: 500 });
  }
}
