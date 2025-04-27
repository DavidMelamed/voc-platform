/**
 * Minimal stub implementation of the Model Context Protocol Server
 * sufficient for running the VOC platform locally without the
 * unpublished “@modelcontextprotocol/server” package.
 *
 * This stub supports:
 *  • defineTool(id, { description, input_schema, handler })
 *  • defineResource(id, { description, uri_pattern, handler })
 *  • expressMiddleware() – returns a pass-through router that exposes
 *    the registered tools & resources for basic debugging only.
 *
 * NOTE:  This is *not* a full MCP implementation – it simply prevents
 * runtime crashes.  Replace with the real package when available.
 */

const express = require("express");

class MCP {
  constructor(name = "mcp-stub") {
    this.name = name;
    this.tools = {};
    this.resources = {};
  }

  defineTool(id, { description = "", input_schema = {}, handler }) {
    if (typeof handler !== "function") {
      throw new Error(`Tool "${id}" requires a handler function`);
    }
    this.tools[id] = { description, input_schema, handler };
  }

  defineResource(id, { description = "", uri_pattern = "", handler }) {
    if (typeof handler !== "function") {
      throw new Error(`Resource "${id}" requires a handler function`);
    }
    this.resources[id] = { description, uri_pattern, handler };
  }

  /**
   * Very thin Express middleware:
   *  • POST /tools/:toolId  – executes the tool’s handler with req.body
   *  • GET  /resources/:resId/:key – executes the resource handler
   *  • GET  /               – lists available tools and resources
   */
  expressMiddleware() {
    const router = express.Router();

    // list everything
    router.get("/", (_req, res) => {
      res.json({
        server: this.name,
        tools: Object.keys(this.tools),
        resources: Object.keys(this.resources),
      });
    });

    // tool invocation
    router.post("/tools/:toolId", async (req, res) => {
      const { toolId } = req.params;
      const tool = this.tools[toolId];
      if (!tool) {
        return res.status(404).json({ error: `Unknown tool ${toolId}` });
      }
      try {
        const result = await tool.handler(req.body || {});
        res.json({ result });
      } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message });
      }
    });

    // resource fetch
    router.get("/resources/:resId/:key", async (req, res) => {
      const { resId, key } = req.params;
      const resource = this.resources[resId];
      if (!resource) {
        return res.status(404).json({ error: `Unknown resource ${resId}` });
      }
      try {
        const result = await resource.handler({ id: key });
        res.json({ result });
      } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.message });
      }
    });

    return router;
  }
}

module.exports = { MCP };
