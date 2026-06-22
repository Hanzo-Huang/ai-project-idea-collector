import type { NextConfig } from "next";
const internalApiUrl = process.env.INTERNAL_API_URL || "http://localhost:8000";
const nextConfig: NextConfig = {
 output: "standalone",
 async rewrites(){
  return [{source:"/backend-api/:path*",destination:`${internalApiUrl}/api/:path*`}];
 },
};
export default nextConfig;
