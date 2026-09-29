import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained .next/standalone build (server.js + only
  // the node_modules actually needed at runtime traced in) instead of
  // requiring the full node_modules tree copied into the runtime image —
  // keeps the production Docker image small and the build reproducible,
  // matching how the FastAPI service is built from a single Dockerfile.
  output: "standalone",
};

export default nextConfig;
