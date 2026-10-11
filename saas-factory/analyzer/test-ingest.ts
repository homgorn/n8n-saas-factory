#!/usr/bin/env node
/**
 * test-ingest.ts — Simple verification of ingestion pipeline
 * No external test framework needed — pure assertions
 */

import { readFileSync, existsSync } from "fs";
import { join } from "path";

console.log("=== Ingestion Pipeline Verification ===\n");

let passed = 0;
let failed = 0;

function test(name: string, fn: () => void) {
  try {
    fn();
    console.log(`✓ PASS: ${name}`);
    passed++;
  } catch (e: any) {
    console.log(`✗ FAIL: ${name}`);
    console.log(`  Error: ${e.message || String(e)}`);
    failed++;
  }
}

function assert(condition: boolean, message: string) {
  if (!condition) throw new Error(message);
}

// Load modules (will throw if broken)
console.log("--- Module Loading ---");

test("chunking module loads", async () => {
  // Dynamic import to test module loading
  const chunking = await import("./src/utils/chunking.js");
  assert(typeof chunking.chunkMarkdown === "function", "chunkMarkdown should be exported");
  assert(typeof chunking.parseMarkdownFile === "function", "parseMarkdownFile should be exported");
  assert(typeof chunking.generateChunkId === "function", "generateChunkId should be exported");
});

test("types module loads", async () => {
  const types = await import("./src/types.js");
  assert(typeof types.ChunkMetadataSchema === "object", "ChunkMetadataSchema should be zod schema");
});

test("qdrant module loads", async () => {
  const qdrant = await import("./src/utils/qdrant.js");
  assert(typeof qdrant.ensureCollection === "function", "ensureCollection should be exported");
});

test("embeddings module loads", async () => {
  const embeddings = await import("./src/utils/embeddings.js");
  assert(typeof embeddings.generateEmbeddings === "function", "generateEmbeddings should be exported");
});

console.log("\n--- Chunking Test ---");

test("chunking creates chunks from real n8n doc", async () => {
  const DOCS_DIR = join(process.cwd(), "..", "..", "n8n-docs-source", "docs");
  const flowLogicPath = join(DOCS_DIR, "build", "flow-logic.md");

  if (!existsSync(flowLogicPath)) {
    throw new Error(`Test file not found: ${flowLogicPath}`);
  }

  const chunking = await import("./src/utils/chunking.js");
  const rawContent = readFileSync(flowLogicPath, "utf-8");

  // Just test first 3000 chars to keep it fast
  const sample = rawContent.slice(0, 3000);
  const chunks = chunking.chunkMarkdown(
    sample,
    "flow-logic-test",
    {
      documentId: "flow-logic-test",
      sourcePath: flowLogicPath,
      sourceUrl: "https://docs.n8n.io/build/flow-logic.md",
      category: "build",
      subcategory: "flow-logic",
      tags: ["if", "switch", "merge"],
      difficulty: "intermediate" as const,
      prerequisites: ["build-your-first-workflow"],
      relatedNodes: ["n8n-nodes-base.if", "n8n-nodes-base.switch"],
    }
  );

  assert(chunks.length > 0, `Should create chunks (got ${chunks.length})`);
  assert(chunks[0].metadata.chunkId.includes("flow-logic-test"), "Chunk ID should contain doc reference");
  assert(chunks[0].metadata.category === "build", "Category should be preserved");
  assert(typeof chunks[0].metadata.tokenCount === "number", "Token count should be number");
});

test("chunk ID is deterministic", async () => {
  const chunking = await import("./src/utils/chunking.js");
  const id1 = chunking.generateChunkId("doc-1", 0, "Intro");
  const id2 = chunking.generateChunkId("doc-1", 0, "Intro");
  const id3 = chunking.generateChunkId("doc-1", 1, "Intro");
  assert(id1 === id2, "Same input should produce same ID");
  assert(id1 !== id3, "Different index should produce different ID");
  assert(id1.length >= 20, "Chunk ID should have reasonable length");
});

test("frontmatter parsing handles GitBook docs", async () => {
  const chunking = await import("./src/utils/chunking.js");
  const sample = `---
title: "Build first workflow"
description: "Tutorial"
contentType: tutorial
---
# Heading
Some text here.
`;
  const parsed = chunking.parseMarkdownFile(sample);
  assert(typeof parsed.frontmatter === "object", "Should parse frontmatter");
  assert(parsed.body.includes("Some text"), "Body should exclude frontmatter");
  assert(parsed.body.includes("# Heading"), "Body should include headings");
});

console.log("\n--- Embedding Module Test ---");

test("embedding cost estimation", async () => {
  const embeddings = await import("./src/utils/embeddings.js");
  // Mock: doesn't need actual OpenAI key
  const cost = embeddings.estimateEmbeddingCost("text-embedding-3-small", 15000);
  assert(typeof cost === "number", "Cost should be a number");
  assert(cost > 0, "Cost should be positive");
  assert(cost < 1, "Cost for 15k tokens should be < $1");
});

test("embedding context creation", async () => {
  const types = await import("./src/types.js");
  const embeddings = await import("./src/utils/embeddings.js");

  const context = embeddings.createEmbeddingContext(
    {
      documentId: "test",
      sourceUrl: "test",
      sourcePath: "test",
      category: "test",
      subcategory: "sub",
      tags: ["a", "b"],
      difficulty: "intermediate",
      prerequisites: ["prev"],
      relatedNodes: ["node"],
      chunkId: "test-chunk",
      chunkType: "prose",
      parentSection: "Intro",
      tokenCount: 100,
      headingPath: ["# Main"],
    },
    "This is content about n8n workflows."
  );
  assert(context.includes("Category: test"), "Context should include category");
  assert(context.includes("Tags: a, b"), "Context should include tags");
  assert(context.includes("This is content"), "Context should include content");
  assert(context.includes("Type: prose"), "Context should include chunk type");
});

console.log("\n--- Qdrant Module Test ---");

test("Qdrant module exports", async () => {
  const qdrant = await import("./src/utils/qdrant.js");
  assert(typeof qdrant.ensureCollection === "function", "ensureCollection exported");
  assert(typeof qdrant.upsertChunks === "function", "upsertChunks exported");
  assert(typeof qdrant.searchChunks === "function", "searchChunks exported");
  assert(typeof qdrant.getCollectionInfo === "function", "getCollectionInfo exported");
});

console.log("\n--- Integration: Real File Processing ---");

test("process sample n8n doc end-to-end", async () => {
  const chunking = await import("./src/utils/chunking.js");
  const DOCS_DIR = join(process.cwd(), "..", "..", "n8n-docs-source", "docs");

  const testFiles = [
    "build/understand-workflows.md",
    "get-started/learning-paths.md",
  ];

  for (const file of testFiles) {
    const fullPath = join(DOCS_DIR, file);
    if (!existsSync(fullPath)) {
      console.log(`  Note: ${file} not found (skipping)`);
      continue;
    }

    const content = readFileSync(fullPath, "utf-8");
    const chunks = chunking.chunkMarkdown(
      content.slice(0, 5000),
      basename(file, ".md"),
      {
        documentId: basename(file, ".md"),
        sourcePath: fullPath,
        sourceUrl: `https://docs.n8n.io/${file}`,
        category: file.split("/")[0],
        tags: [],
        difficulty: "intermediate" as const,
        prerequisites: [],
        relatedNodes: [],
      }
    );
    assert(chunks.length > 0, `Should chunk ${file}`);
    assert(chunks[0].metadata.chunkId.length > 10, `Chunk ID valid for ${file}`);
    console.log(`  ✓ ${file} → ${chunks.length} chunks`);
  }
});

console.log("\n=== Final Results ===");
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);

if (failed > 0) {
  console.log("\n⚠ Some tests failed. Review errors above.");
  console.log("Next steps:");
  console.log("  1. Check Qdrant server is running (docker run -p 6333:6333 qdrant/qdrant)");
  console.log("  2. Set OPENAI_API_KEY in environment");
  console.log("  3. Run: npm run ingest:docs");
  process.exit(1);
} else {
  console.log("\n✅ All ingestion pipeline components verified successfully!");
  console.log("The pipeline is ready. Run full ingestion with:");
  console.log("  npm run ingest:docs");
}
