import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  images: {
    remotePatterns: [
      new URL("https://danadairymystotage.blob.core.windows.net/**"),
    ],
  },
};

export default nextConfig;
