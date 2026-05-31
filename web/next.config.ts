import type { NextConfig } from "next";

const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";
// Use absolute URL for assetPrefix so _next/static/ assets are fetched directly
// from Vercel CDN, bypassing the legislature-dashboard proxy (which can't rewrite
// _next/ paths due to Vercel CDN special-casing them).
const assetPrefix = process.env.NEXT_PUBLIC_ASSET_PREFIX ?? basePath;

const nextConfig: NextConfig = {
  output: "export",
  basePath,
  assetPrefix,
  images: { unoptimized: true },
};

export default nextConfig;
