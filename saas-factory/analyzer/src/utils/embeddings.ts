import OpenAI from "openai";
import { ChunkMetadata } from "../types.js";

export interface EmbeddingConfig {
  apiKey: string;
  model: "text-embedding-3-small" | "text-embedding-3-large" | "text-embedding-ada-002";
  dimensions?: number; // Only for text-embedding-3 models
  batchSize: number;
  maxRetries: number;
  retryDelayMs: number;
}

let openai: OpenAI | null = null;

function getOpenAI(config: EmbeddingConfig): OpenAI {
  if (!openai) {
    openai = new OpenAI({
      apiKey: config.apiKey,
      maxRetries: config.maxRetries,
    });
  }
  return openai;
}

export async function generateEmbeddings(
  config: EmbeddingConfig,
  texts: string[]
): Promise<number[][]> {
  const client = getOpenAI(config);
  const allEmbeddings: number[][] = [];

  // Process in batches
  for (let i = 0; i < texts.length; i += config.batchSize) {
    const batch = texts.slice(i, i + config.batchSize);
    let retries = 0;

    while (retries <= config.maxRetries) {
      try {
        const response = await client.embeddings.create({
          model: config.model,
          input: batch,
          dimensions: config.dimensions,
          encoding_format: "float",
        });

        const embeddings = response.data
          .sort((a, b) => a.index - b.index)
          .map((d) => d.embedding);

        allEmbeddings.push(...embeddings);
        break;
      } catch (error) {
        retries++;
        if (retries > config.maxRetries) {
          throw new Error(`Failed to generate embeddings after ${config.maxRetries} retries: ${error}`);
        }
        console.warn(`Embedding batch failed, retry ${retries}/${config.maxRetries}:`, error);
        await new Promise((resolve) => setTimeout(resolve, config.retryDelayMs * retries));
      }
    }
  }

  return allEmbeddings;
}

export async function generateSingleEmbedding(
  config: EmbeddingConfig,
  text: string
): Promise<number[]> {
  const embeddings = await generateEmbeddings(config, [text]);
  return embeddings[0];
}

/** Estimate cost for embedding generation */
export function estimateEmbeddingCost(
  model: EmbeddingConfig["model"],
  totalTokens: number
): number {
  const costPer1kTokens: Record<EmbeddingConfig["model"], number> = {
    "text-embedding-3-small": 0.00002,
    "text-embedding-3-large": 0.00013,
    "text-embedding-ada-002": 0.0001,
  };
  return (totalTokens / 1000) * costPer1kTokens[model];
}

/** Validate embedding dimensions */
export function validateEmbeddingDimensions(
  embedding: number[],
  expectedDimensions: number
): boolean {
  return embedding.length === expectedDimensions;
}

/** Chunk metadata for embedding context */
export function createEmbeddingContext(metadata: ChunkMetadata, content: string): string {
  const parts: string[] = [];

  // Add category context
  if (metadata.category) {
    parts.push(`Category: ${metadata.category}`);
  }
  if (metadata.subcategory) {
    parts.push(`Subcategory: ${metadata.subcategory}`);
  }

  // Add tags
  if (metadata.tags.length > 0) {
    parts.push(`Tags: ${metadata.tags.join(", ")}`);
  }

  // Add related nodes
  if (metadata.relatedNodes.length > 0) {
    parts.push(`Related nodes: ${metadata.relatedNodes.join(", ")}`);
  }

  // Add section context
  if (metadata.parentSection) {
    parts.push(`Section: ${metadata.parentSection}`);
  }
  if (metadata.headingPath.length > 0) {
    parts.push(`Path: ${metadata.headingPath.join(" > ")}`);
  }

  // Add chunk type context
  parts.push(`Type: ${metadata.chunkType}`);

  // Add content
  parts.push(`Content: ${content}`);

  return parts.join("\n");
}