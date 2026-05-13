import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import cors from "cors";
import type { Request, Response } from "express";
import { createServer } from "./server.js";

const LOCAL_CORS_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);

function configuredOrigins(): Set<string> {
  return new Set(
    (process.env.MCP_APP_ALLOWED_ORIGINS ?? "")
      .split(",")
      .map((origin) => origin.trim())
      .filter(Boolean),
  );
}

function isAllowedOrigin(origin: string | undefined, configured: Set<string>): boolean {
  if (!origin) return true;
  if (configured.has(origin)) return true;

  try {
    const parsed = new URL(origin);
    return LOCAL_CORS_HOSTS.has(parsed.hostname);
  } catch {
    return false;
  }
}

export async function startStreamableHTTPServer(
  createServerInstance: () => McpServer,
): Promise<void> {
  const port = parseInt(process.env.PORT ?? "3001", 10);
  const host = process.env.MCP_APP_HOST ?? "127.0.0.1";
  const app = createMcpExpressApp({ host });
  const origins = configuredOrigins();

  app.use(cors({
    origin(origin, callback) {
      if (isAllowedOrigin(origin, origins)) {
        callback(null, true);
        return;
      }
      callback(new Error(`CORS origin not allowed: ${origin}`));
    },
  }));
  app.all("/mcp", async (req: Request, res: Response) => {
    const server = createServerInstance();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });

    res.on("close", () => {
      transport.close().catch(() => {});
      server.close().catch(() => {});
    });

    try {
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
    } catch (error) {
      console.error("MCP error:", error);
      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: { code: -32603, message: "Internal server error" },
          id: null,
        });
      }
    }
  });

  const httpServer = app.listen(port, host, () => {
    console.log(`MCP server listening on http://${host}:${port}/mcp`);
  });

  httpServer.on("error", (error: Error) => {
    console.error("Failed to start MCP server:", error);
    process.exit(1);
  });

  const shutdown = () => {
    console.log("\nShutting down...");
    httpServer.close(() => process.exit(0));
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

export async function startStdioServer(
  createServerInstance: () => McpServer,
): Promise<void> {
  await createServerInstance().connect(new StdioServerTransport());
}

async function main() {
  if (process.argv.includes("--stdio")) {
    await startStdioServer(createServer);
  } else {
    await startStreamableHTTPServer(createServer);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
