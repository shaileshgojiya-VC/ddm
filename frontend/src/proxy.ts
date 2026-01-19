import { NextRequest, NextResponse } from "next/server";
import { auth } from "./utils/auth";

/* -------------------- CONFIG -------------------- */

const PUBLIC_PATHS = [
  "/login",
  "/forgot-password",
  "/reset-password",
  "/unauthorized",
];

const UNIVERSAL_ROUTES = ["profile", "change-password", "unauthorized"];

const DEFAULT_MODULE = "dashboard";

/* -------------------- HELPERS -------------------- */

function getModuleFromPath(pathname: string): string | null {
  const segment = pathname.split("/").filter(Boolean)[0];
  return segment ?? null;
}

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`)
  );
}

function isUniversalRoute(pathname: string): boolean {
  const routeModule = getModuleFromPath(pathname);
  return routeModule ? UNIVERSAL_ROUTES.includes(routeModule) : false;
}

function getDefaultRedirect(modules: string[]): string {
  if (modules.includes(DEFAULT_MODULE)) {
    return `/${DEFAULT_MODULE}`;
  }
  if (modules.length > 0) {
    return `/${modules[0]}`;
  }
  return "/unauthorized";
}

/* -------------------- PROXY -------------------- */

export async function proxy(request: NextRequest) {
  const session = await auth();
  const pathname = request.nextUrl.pathname;

  /* ---- ALWAYS ALLOW UNAUTHORIZED PAGE ---- */
  if (pathname === "/unauthorized") {
    return NextResponse.next();
  }

  const isPublic = isPublicPath(pathname);

  /* ---- EXTRACT MODULE LIST SAFELY ---- */
  const activeRoleName = session?.role?.name;

  const activeRole = session?.roles?.find(
    (role) => role.name === activeRoleName
  );

  const userModules: string[] = activeRole?.module_list ?? [];

  /* ---- FORCE PASSWORD CHANGE ---- */
  if (session?.requiresPasswordChange && pathname !== "/change-password") {
    return NextResponse.redirect(new URL("/change-password", request.url));
  }

  /* ---- ROOT ROUTE ---- */
  if (pathname === "/") {
    return NextResponse.redirect(
      new URL(session ? getDefaultRedirect(userModules) : "/login", request.url)
    );
  }

  /* ---- AUTH GUARD ---- */
  if (!session && !isPublic) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  /* ---- MODULE AUTHORIZATION ---- */
  if (session && !isPublic && !isUniversalRoute(pathname)) {
    const requiredModule = getModuleFromPath(pathname)?.toLowerCase();

    if (
      requiredModule &&
      !userModules.map((m) => m.toLowerCase()).includes(requiredModule)
    ) {
      return NextResponse.redirect(new URL("/unauthorized", request.url));
    }
  }

  return NextResponse.next();
}

/* -------------------- MATCHER -------------------- */

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|.*\\..*).*)"],
};
