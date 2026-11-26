import { NextResponse, type NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  if (!req.cookies.get("fd_token")) {
    // Relative redirect: behind nginx, req.url can carry the internal
    // host (localhost:3100), so never build an absolute URL from it.
    return new NextResponse(null, { status: 307, headers: { Location: "/login" } });
  }
  return NextResponse.next();
}

export const config = { matcher: ["/((?!login|_next|favicon.ico).*)"] };