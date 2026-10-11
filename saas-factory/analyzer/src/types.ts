import { z } from "zod";

/** Frontmatter schema from n8n docs */
export const FrontmatterSchema = z.object({
  title: z.string().optional(),
  description: z.string().optional(),
  contentType: z.enum(["howto", "reference", "overview", "tutorial", "concept"]).optional(),
  search: z.boolean().optional(),
  hide: z.array(z.string()).optional(),
  /** Custom n8n fields */
  nodeType: z.string().optional(),
  nodeCategories: z.array(z.string()).optional(),
  operations: z.array(z.string()).optional(),
  credentials: z.array(z.string()).optional(),
  /** Our enriched fields */
  category: z.string().optional(),
  subcategory: z.string().optional(),
  tags: z.array(z.string()).optional(),
  difficulty: z.enum(["beginner", "intermediate", "advanced"]).optional(),
  prerequisites: z.array(z.string()).optional(),
  relatedNodes: z.array(z.string()).optional(),
  codeExamples: z.boolean().optional(),
  hasWorkflowTemplate: z.boolean().optional(),
  lastUpdated: z.string().optional(),
  version: z.string().optional(),
}).passthrough();

export type Frontmatter = z.infer<typeof FrontmatterSchema>;

/** Chunk metadata for vector DB */
export const ChunkMetadataSchema = z.object({
  documentId: z.string(),
  sourceUrl: z.string(),
  sourcePath: z.string(),
  category: z.string(),
  subcategory: z.string().optional(),
  tags: z.array(z.string()),
  difficulty: z.enum(["beginner", "intermediate", "advanced"]),
  prerequisites: z.array(z.string()),
  relatedNodes: z.array(z.string()),
  chunkId: z.string(),
  chunkType: z.enum(["prose", "code_example", "configuration", "warning", "tip", "table", "header"]),
  parentSection: z.string().optional(),
  tokenCount: z.number(),
  headingPath: z.array(z.string()),
  /** Original frontmatter */
  frontmatter: FrontmatterSchema.optional(),
});

export type ChunkMetadata = z.infer<typeof ChunkMetadataSchema>;

/** Document record for tracking */
export const DocumentRecordSchema = z.object({
  documentId: z.string(),
  sourcePath: z.string(),
  sourceUrl: z.string(),
  title: z.string(),
  category: z.string(),
  subcategory: z.string().optional(),
  tags: z.array(z.string()),
  difficulty: z.enum(["beginner", "intermediate", "advanced"]),
  chunkCount: z.number(),
  totalTokens: z.number(),
  lastUpdated: z.string(),
  hash: z.string(), // content hash for change detection
});

export type DocumentRecord = z.infer<typeof DocumentRecordSchema>;

/** Ingestion stats */
export interface IngestionStats {
  filesProcessed: number;
  chunksCreated: number;
  chunksEmbedded: number;
  chunksStored: number;
  errors: Array<{ file: string; error: string }>;
  startTime: Date;
  endTime?: Date;
}

/** Qdrant point payload */
export interface QdrantPayload extends ChunkMetadata {
  text: string;
}

/** Search result */
export interface SearchResult {
  id: string;
  score: number;
  payload: QdrantPayload;
}