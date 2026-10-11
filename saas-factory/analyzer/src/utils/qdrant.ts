import { QdrantClient } from "@qdrant/js-client-rest";
import { ChunkMetadata, QdrantPayload, SearchResult } from "../types.js";
import { createHash } from "crypto";

export interface QdrantConfig {
  url: string;
  apiKey?: string;
  collectionName: string;
  vectorSize: number;
  distance?: "Cosine" | "Euclid" | "Dot";
}

let client: QdrantClient | null = null;

export function getQdrantClient(config: QdrantConfig): QdrantClient {
  if (!client) {
    client = new QdrantClient({
      url: config.url,
      apiKey: config.apiKey,
    });
  }
  return client;
}

export async function ensureCollection(config: QdrantConfig): Promise<void> {
  const qdrant = getQdrantClient(config);

  const collections = await qdrant.getCollections();
  const exists = collections.collections.some((c) => c.name === config.collectionName);

  if (!exists) {
    console.log(`Creating collection: ${config.collectionName}`);
    await qdrant.createCollection(config.collectionName, {
      vectors: {
        size: config.vectorSize,
        distance: config.distance || "Cosine",
      },
      optimizers_config: {
        default_segment_number: 2,
      },
      hnsw_config: {
        m: 16,
        ef_construct: 100,
      },
    });

    // Create payload indexes for filtering
    await Promise.all([
      qdrant.createPayloadIndex(config.collectionName, {
        field_name: "category",
        field_schema: "keyword",
      }),
      qdrant.createPayloadIndex(config.collectionName, {
        field_name: "subcategory",
        field_schema: "keyword",
      }),
      qdrant.createPayloadIndex(config.collectionName, {
        field_name: "tags",
        field_schema: "keyword",
      }),
      qdrant.createPayloadIndex(config.collectionName, {
        field_name: "difficulty",
        field_schema: "keyword",
      }),
      qdrant.createPayloadIndex(config.collectionName, {
        field_name: "chunkType",
        field_schema: "keyword",
      }),
      qdrant.createPayloadIndex(config.collectionName, {
        field_name: "relatedNodes",
        field_schema: "keyword",
      }),
    ]);

    console.log(`Collection ${config.collectionName} created with indexes`);
  } else {
    console.log(`Collection ${config.collectionName} already exists`);
  }
}

export async function upsertChunks(
  config: QdrantConfig,
  chunks: Array<{ content: string; metadata: ChunkMetadata; embedding: number[] }>
): Promise<number> {
  const qdrant = getQdrantClient(config);

  const points = chunks.map(({ content, metadata, embedding }) => ({
    id: metadata.chunkId,
    vector: embedding,
    payload: {
      ...metadata,
      text: content,
    } as QdrantPayload,
  }));

  // Batch upsert in chunks of 100
  const batchSize = 100;
  let upserted = 0;

  for (let i = 0; i < points.length; i += batchSize) {
    const batch = points.slice(i, i + batchSize);
    await qdrant.upsert(config.collectionName, {
      wait: true,
      points: batch,
    });
    upserted += batch.length;
    console.log(`  Upserted ${upserted}/${points.length} points`);
  }

  return upserted;
}

export async function searchChunks(
  config: QdrantConfig,
  queryVector: number[],
  options: {
    limit?: number;
    filter?: Record<string, unknown>;
    withPayload?: boolean;
  } = {}
): Promise<SearchResult[]> {
  const qdrant = getQdrantClient(config);

  const result = await qdrant.search(config.collectionName, {
    vector: queryVector,
    limit: options.limit || 10,
    filter: options.filter,
    with_payload: options.withPayload !== false,
    with_vector: false,
  });

  return result.map((r) => ({
    id: r.id as string,
    score: r.score,
    payload: r.payload as QdrantPayload,
  }));
}

export async function scrollChunks(
  config: QdrantConfig,
  options: {
    limit?: number;
    filter?: Record<string, unknown>;
    offset?: string | number;
  } = {}
): Promise<{ points: SearchResult[]; nextOffset: string | number | null }> {
  const qdrant = getQdrantClient(config);

  const result = await qdrant.scroll(config.collectionName, {
    limit: options.limit || 100,
    filter: options.filter,
    offset: options.offset,
    with_payload: true,
    with_vector: false,
  });

  return {
    points: result.points.map((p) => ({
      id: p.id as string,
      score: 1,
      payload: p.payload as QdrantPayload,
    })),
    nextOffset: result.next_page_offset ?? null,
  };
}

export async function deleteChunksByDocumentId(
  config: QdrantConfig,
  documentId: string
): Promise<number> {
  const qdrant = getQdrantClient(config);

  const result = await qdrant.delete(config.collectionName, {
    wait: true,
    filter: {
      must: [
        {
          key: "documentId",
          match: { value: documentId },
        },
      ],
    },
  });

  return result.operation_id ? 1 : 0;
}

export async function getCollectionInfo(config: QdrantConfig): Promise<{
  pointsCount: number;
  vectorsCount: number;
  segmentsCount: number;
  status: string;
}> {
  const qdrant = getQdrantClient(config);
  const info = await qdrant.getCollection(config.collectionName);
  return {
    pointsCount: info.points_count ?? 0,
    vectorsCount: info.vectors_count ?? 0,
    segmentsCount: info.segments_count ?? 0,
    status: info.status,
  };
}

/** Generate deterministic point ID from documentId + chunkIndex */
export function generatePointId(documentId: string, chunkIndex: number): string {
  return createHash("md5").update(`${documentId}-${chunkIndex}`).digest("hex");
}