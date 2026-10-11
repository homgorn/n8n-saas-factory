#!/usr/bin/env node
/**
 * ingest-docs.ts — Main ingestion pipeline for n8n documentation
 * Processes docs/ directory, chunks, embeds, stores in Qdrant
 */

import { readdirSync, statSync, readFileSync, existsSync } from "fs";
import { join, basename, dirname } from "path";
import matter from "gray-matter";
import { createHash } from "crypto";
import ora from "ora";
import chalk from "chalk";
import { chunkMarkdown, parseMarkdownFile } from "./utils/chunking.js";
import { generateEmbeddings } from "./utils/embeddings.js";
import {
  ensureCollection,
  upsertChunks,
  getCollectionInfo,
  QdrantConfig,
} from "./utils/qdrant.js";
import { ChunkMetadata, ChunkMetadataSchema } from "./types.js";

const DOCS_DIR = join(process.cwd(), "..", "n8n-docs-source", "docs");

const EMBEDDING_CONFIG = {
  apiKey: process.env.OPENAI_API_KEY || "sk-test-placeholder",
  model: (process.env.EMBEDDING_MODEL as any) || "text-embedding-3-small",
  batchSize: parseInt(process.env.EMBED_BATCH_SIZE || "50"),
  maxRetries: parseInt(process.env.EMBED_MAX_RETRIES || "3"),
  retryDelayMs: parseInt(process.env.EMBED_RETRY_DELAY || "1000"),
};

const QDRANT_CONFIG: QdrantConfig = {
  url: process.env.QDRANT_URL || "http://localhost:6333",
  apiKey: process.env.QDRANT_API_KEY,
  collectionName: process.env.QDRANT_COLLECTION || "n8n_knowledge_base",
  vectorSize: parseInt(process.env.VECTOR_SIZE || "1536"),
  distance: (process.env.VECTOR_DISTANCE as any) || "Cosine",
};

interface IngestionResult {
  filesProcessed: number;
  filesFailed: number;
  chunksCreated: number;
  chunksEmbedded: number;
  chunksStored: number;
  errors: Array<{ file: string; error: string }>
  totalTokens: number;
  startTime: Date;
  endTime: Date;
  durationMs: number;
}

function listMarkdownFiles(dir: string, baseDir = dir): string[] {
  const files: string[] = [];
  const entries = readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      // Skip hidden/config directories
      if (entry.name.startsWith(".") || entry.name === ".gitbook") continue;
      files.push(...listMarkdownFiles(fullPath, baseDir));
    } else if (entry.isFile() && entry.name.endsWith(".md")) {
      files.push(fullPath);
    }
  }
  return files;
}

function extractCategoryFromPath(filePath: string): string {
  const relativePath = filePath.replace(DOCS_DIR + "\\", "").replace(DOCS_DIR + "/", "");
  const parts = relativePath.split(/[\\\/]/);
  const firstDir = parts[0] || "other";
  return firstDir;
}

function runIngestion(): IngestionResult {
  const spinner = ora({ text: "Initializing ingestion...", color: "cyan" }).start();
  const result: IngestionResult = {
    filesProcessed: 0,
    filesFailed: 0,
    chunksCreated: 0,
    chunksEmbedded: 0,
    chunksStored: 0,
    errors: [],
    totalTokens: 0,
    startTime: new Date(),
    endTime: new Date(),
    durationMs: 0,
  };

  try {
    // 1. Initialize Qdrant
    spinner.text = "Ensuring Qdrant collection...";
    if (!existsSync(DOCS_DIR)) {
      throw new Error(`Docs directory not found: ${DOCS_DIR}`);
    }
    ensureCollection(QDRANT_CONFIG).catch((e) => {
      console.warn(chalk.yellow("Qdrant connection failed, will retry during upsert"), e);
    });

    // 2. List all markdown files
    spinner.text = "Scanning documentation files...";
    const files = listMarkdownFiles(DOCS_DIR);
    spinner.succeed(chalk.green(`Found ${files.length} markdown files`));

    const allChunks: Array<{
      content: string;
      metadata: ChunkMetadata;
    }> = [];

    // 3. Process each file
    for (let i = 0; i < files.length; i++) {
      const filePath = files[i];
      const relativePath = filePath.replace(DOCS_DIR + (process.platform === "win32" ? "\\" : "/"), "");

      spinner.text = `Processing (${i + 1}/${files.length}): ${basename(relativePath)}`;

      try {
        // Read file
        const rawContent = readFileSync(filePath, "utf-8");

        // Parse frontmatter and body
        const { frontmatter, body } = parseMarkdownFile(rawContent);
        const category = extractCategoryFromPath(filePath);
        const documentId = basename(filePath, ".md");

        // Chunk the content
        const chunks = chunkMarkdown(
          body,
          documentId,
          {
            documentId,
            sourcePath: filePath,
            sourceUrl: `https://docs.n8n.io/${relativePath.replace("\\", "/")}`,
            category,
            subcategory: category, // Default to same as category
            tags: [],
            difficulty: "intermediate" as const,
            prerequisites: [],
            relatedNodes: [],
          }
        );

        result.filesProcessed++;
        result.chunksCreated += chunks.length;
        result.totalTokens += chunks.reduce((sum, c) => sum + c.metadata.tokenCount, 0);

        for (const chunk of chunks) {
          allChunks.push({
            content: chunk.content,
            metadata: chunk.metadata,
          });
        }
      } catch (error) {
        result.filesFailed++;
        result.errors.push({
          file: filePath,
          error: error instanceof Error ? error.message : String(error),
        });
        console.warn(chalk.yellow(`Failed: ${basename(filePath)} - ${error}`));
      }
    }

    spinner.text = `Creating embeddings for ${allChunks.length} chunks...`;

    // 4. Generate embeddings in batches
    const chunkContents = allChunks.map((c) => c.content);
    const embeddings = await generateEmbeddings(EMBEDDING_CONFIG, chunkContents);
    result.chunksEmbedded = embeddings.length;

    spinner.text = `Storing ${embeddings.length} chunks in Qdrant...`;

    // 5. Store in Qdrant
    const chunksWithEmbeddings = allChunks.map((chunk, index) => ({
      ...chunk,
      embedding: embeddings[index],
    }));

    await ensureCollection(QDRANT_CONFIG);
    result.chunksStored = await upsertChunks(QDRANT_CONFIG, chunksWithEmbeddings);
    spinner.succeed(chalk.green(`Stored ${result.chunksStored} chunks`));

    // 6. Final stats
    result.endTime = new Date();
    result.durationMs = result.endTime.getTime() - result.startTime.getTime();

    spinner.succeed(
      chalk.green(
        `Ingestion complete! Files: ${result.filesProcessed}, ` +
          `Chunks: ${result.chunksCreated}, Embedded: ${result.chunksEmbedded}, ` +
          `Stored: ${result.chunksStored}, Errors: ${result.errors.length}, ` +
          `Time: ${(result.durationMs / 1000).toFixed(1)}s`
      )
    );

    // 7. Print summary
    console.log(chalk.cyan("\n=== Ingestion Summary ==="));
    console.log(chalk.green(`✓ Files processed: ${result.filesProcessed}`));
    console.log(chalk.green(`✓ Chunks created: ${result.chunksCreated}`));
    console.log(chalk.green(`✓ Embeddings generated: ${result.chunksEmbedded}`));
    console.log(chalk.green(`✓ Chunks stored: ${result.chunksStored}`));
    console.log(chalk.yellow(`⚠ Errors: ${result.errors.length}`));
    if (result.errors.length > 0) {
      console.log(chalk.yellow("Failed files:"));
      for (const err of result.errors.slice(0, 5)) {
        console.log(chalk.yellow(`  - ${basename(err.file)}: ${err.error}`));
      }
      if (result.errors.length > 5) {
        console.log(chalk.yellow(`  ... and ${result.errors.length - 5} more`));
      }
    }
    console.log(chalk.cyan(`⏱ Duration: ${(result.durationMs / 1000).toFixed(2)}s`));

  } catch (error) {
    spinner.fail(chalk.red(`Ingestion failed: ${error}`));
    result.errors.push({ file: "global", error: String(error) });
  }

  return result;
}

// Helper: parseMarkdownFile for ingest-docs
function parseMarkdownFile(fileContent: string): { frontmatter: Record<string, unknown>; body: string } {
  const grayMatter = require("gray-matter");
  try {
    const parsed = grayMatter(fileContent);
    return {
      frontmatter: parsed.data || {},
      body: parsed.content || fileContent,
    };
  } catch {
    return { frontmatter: {}, body: fileContent };
  }
}

// Main execution
if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.includes("ingest-docs")) {
  console.log(chalk.cyan("=== n8n Documentation Ingestion Pipeline ==="));
  console.log(chalk.gray(`Starting at ${new Date().toISOString()}`));
  console.log(chalk.gray(`Source: ${DOCS_DIR}`));
  console.log(chalk.gray(`Target Collection: ${QDRANT_CONFIG.collectionName}`));

  const stats = runIngestion();

  // Write stats to file
  const fs = await import("fs/promises");
  await fs.default.writeFile(
    join(process.cwd(), "n8n-wiki", "metadata", "last-ingest.json"),
    JSON.stringify(
      {
        ...stats,
        timestamp: new Date().toISOString(),
        version: "1.0",
        sourceDir: DOCS_DIR,
      },
      null,
      2
    )
  );

  console.log(chalk.green("\n✅ Results saved to n8n-wiki/metadata/last-ingest.json"));
  process.exit(stats.errors.length > 0 ? 1 : 0);
}

export { runIngestion, listMarkdownFiles };
