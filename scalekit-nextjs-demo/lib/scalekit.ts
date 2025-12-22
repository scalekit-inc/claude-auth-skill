import { Scalekit } from '@scalekit-sdk/node';

if (!process.env.SCALEKIT_ENVIRONMENT_URL) {
  throw new Error('SCALEKIT_ENVIRONMENT_URL is not defined');
}

if (!process.env.SCALEKIT_CLIENT_ID) {
  throw new Error('SCALEKIT_CLIENT_ID is not defined');
}

if (!process.env.SCALEKIT_CLIENT_SECRET) {
  throw new Error('SCALEKIT_CLIENT_SECRET is not defined');
}

// Initialize Scalekit client
export const scalekit = new Scalekit(
  process.env.SCALEKIT_ENVIRONMENT_URL,
  process.env.SCALEKIT_CLIENT_ID,
  process.env.SCALEKIT_CLIENT_SECRET
);

// Application URLs
export const CALLBACK_URL = process.env.CALLBACK_URL!;
export const POST_LOGOUT_URL = process.env.POST_LOGOUT_URL!;

// Cookie configuration
export const cookieConfig = {
  httpOnly: true,
  secure: process.env.COOKIE_SECURE === 'true',
  sameSite: 'strict' as const,
  path: '/',
};
