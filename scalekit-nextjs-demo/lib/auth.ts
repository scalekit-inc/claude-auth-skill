import { cookies } from "next/headers";
import { scalekit, cookieConfig } from "./scalekit";
import { redirect } from "next/navigation";

export interface User {
  sub: string;
  email: string;
  email_verified?: boolean;
  name?: string;
  given_name?: string;
  family_name?: string;
}

/**
 * Get the current user from cookies
 * Returns null if not authenticated
 */
export async function getCurrentUser(): Promise<User | null> {
  const cookieStore = await cookies();
  const userCookie = cookieStore.get("user");

  if (!userCookie) {
    return null;
  }

  try {
    return JSON.parse(userCookie.value) as User;
  } catch {
    return null;
  }
}

/**
 * Validate access token and return claims
 * Throws error if token is invalid or expired
 */
export async function getValidatedClaims() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("accessToken")?.value;

  if (!accessToken) {
    throw new Error("No access token found");
  }

  try {
    const claims = await scalekit.validateToken(accessToken, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL,
      audience: process.env.SCALEKIT_CLIENT_ID,
    });
    return claims;
  } catch (error) {
    throw new Error("Invalid or expired access token");
  }
}

/**
 * Require authentication for server components/actions
 * Redirects to login if not authenticated or token is invalid
 */
export async function requireAuth() {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("accessToken")?.value;

  if (!accessToken) {
    redirect("/auth/login");
  }

  try {
    const claims = await scalekit.validateToken(accessToken, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL,
      audience: process.env.SCALEKIT_CLIENT_ID,
    });
    return claims;
  } catch (error) {
    // Token invalid or expired - redirect to login
    // Note: Token refresh cannot be done in server components
    // User will need to re-authenticate
    redirect("/auth/login");
  }
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("accessToken")?.value;

  if (!accessToken) {
    return false;
  }

  try {
    await scalekit.validateToken(accessToken, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL,
      audience: process.env.SCALEKIT_CLIENT_ID,
    });
    return true;
  } catch {
    return false;
  }
}
