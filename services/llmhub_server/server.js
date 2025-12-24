// Minimal llmhub-node HTTP server.
// Adjust import paths if your llmhub-node exports differ.

import express from "express";
import { createHub, Provider, httpHandlers } from "@volpestyle/llmhub-node";

const app = express();
app.use(express.json({ limit: "10mb" }));

const hub = createHub({
  providers: {
    [Provider.OpenAI]: { apiKey: process.env.OPENAI_API_KEY },
  },
});

const handlers = httpHandlers(hub);

app.get("/provider-models", handlers.models());
app.post("/generate", handlers.generate());
app.post("/generate/stream", handlers.generateSSE());

const port = process.env.PORT ? Number(process.env.PORT) : 8787;
app.listen(port, () => console.log(`llmhub server listening on http://localhost:${port}`));
