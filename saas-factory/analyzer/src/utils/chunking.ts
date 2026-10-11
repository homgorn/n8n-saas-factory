import MarkdownIt from "markdown-it";
import { ChunkMetadata, ChunkMetadataSchema } from "../types.js";
import { v4 as uuidv4 } from "uuid";
import { createHash } from "crypto";

const md = new MarkdownIt({ html: true, linkify: true, typographer: true });

/** Token estimation: ~4 chars per token for English */
export function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

/** Generate deterministic chunk ID */
export function generateChunkId(documentId: string, index: number, sectionTitle: string): string {
  const hash = createHash("md5").update(`${documentId}-${index}-${sectionTitle}`).digest("hex").slice(0, 8);
  return `${documentId}-chunk-${index}-${hash}`;
}

/** Extract heading path from token stream */
export function extractHeadingPath(tokens: MarkdownIt.Token[], currentIndex: number): string[] {
  const path: string[] = [];
  for (let i = currentIndex; i >= 0; i--) {
    const token = tokens[i];
    if (token.type === "heading_open") {
      const level = parseInt(token.tag.slice(1), 10);
      const nextToken = tokens[i + 1];
      if (nextToken && nextToken.type === "inline") {
        path.unshift(`${"#".repeat(level)} ${nextToken.content}`);
      }
    }
  }
  return path;
}

/** Determine chunk type from content */
export function determineChunkType(content: string, tokens: MarkdownIt.Token[], index: number): ChunkMetadata["chunkType"] {
  const token = tokens[index];
  if (!token) return "prose";

  // Code blocks
  if (token.type === "fence" || token.type === "code_block") {
    return "code_example";
  }

  // Tables
  if (token.type === "table_open") {
    return "table";
  }

  // Headers
  if (token.type === "heading_open") {
    return "header";
  }

  // Check for warning/tip patterns in content
  const lower = content.toLowerCase();
  if (lower.includes("warning") || lower.includes("⚠") || lower.includes("caution")) {
    return "warning";
  }
  if (lower.includes("tip") || lower.includes("💡") || lower.includes("hint") || lower.includes("note")) {
    return "tip";
  }
  if (lower.includes("config") || lower.includes("environment variable") || lower.includes("setting")) {
    return "configuration";
  }

  return "prose";
}

/** Semantic chunking: split by headers, keep code blocks intact */
export function chunkMarkdown(
  content: string,
  documentId: string,
  baseMetadata: Partial<ChunkMetadata>
): Array<{ content: string; metadata: ChunkMetadata }> {
  const tokens = md.parse(content, {});
  const chunks: Array<{ content: string; metadata: ChunkMetadata }> = [];

  let currentChunk = "";
  let currentSectionTitle = "";
  let currentHeadingPath: string[] = [];
  let chunkIndex = 0;
  let inCodeBlock = false;
  let codeBlockContent = "";

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];

    // Track code blocks
    if (token.type === "fence" || token.type === "code_block") {
      inCodeBlock = true;
      codeBlockContent = token.content;
    }

    // Track headers
    if (token.type === "heading_open") {
      const nextToken = tokens[i + 1];
      if (nextToken && nextToken.type === "inline") {
        currentSectionTitle = nextToken.content;
        currentHeadingPath = extractHeadingPath(tokens, i);
      }
    }

    // Render token to string
    const rendered = md.renderer.renderToken(tokens, i, {});

    // Decide whether to split
    const shouldSplit =
      !inCodeBlock &&
      (token.type === "heading_open" && i > 0) && // New section
      currentChunk.length > 500; // Minimum chunk size

    if (shouldSplit && currentChunk.trim().length > 0) {
      const chunkId = generateChunkId(documentId, chunkIndex, currentSectionTitle);
      const chunkType = determineChunkType(currentChunk, tokens, i);
      const tokenCount = estimateTokens(currentChunk);

      chunks.push({
        content: currentChunk.trim(),
        metadata: ChunkMetadataSchema.parse({
          ...baseMetadata,
          chunkId,
          chunkType,
          parentSection: currentSectionTitle || undefined,
          tokenCount,
          headingPath: currentHeadingPath,
        }),
      });

      chunkIndex++;
      currentChunk = "";
    }

    currentChunk += rendered;

    // End code block
    if (inCodeBlock && (token.type === "fence" || token.type === "code_block")) {
      inCodeBlock = false;
      // Code block is its own chunk if substantial
      if (codeBlockContent.trim().length > 50) {
        const chunkId = generateChunkId(documentId, chunkIndex, `code-${chunkIndex}`);
        const tokenCount = estimateTokens(codeBlockContent);

        chunks.push({
          content: codeBlockContent.trim(),
          metadata: ChunkMetadataSchema.parse({
            ...baseMetadata,
            chunkId,
            chunkType: "code_example",
            parentSection: currentSectionTitle || undefined,
            tokenCount,
            headingPath: currentHeadingPath,
          }),
        });
        chunkIndex++;
      }
    }
  }

  // Final chunk
  if (currentChunk.trim().length > 0) {
    const chunkId = generateChunkId(documentId, chunkIndex, currentSectionTitle || "end");
    const chunkType = determineChunkType(currentChunk, tokens, tokens.length - 1);
    const tokenCount = estimateTokens(currentChunk);

    chunks.push({
      content: currentChunk.trim(),
      metadata: ChunkMetadataSchema.parse({
        ...baseMetadata,
        chunkId,
        chunkType,
        parentSection: currentSectionTitle || undefined,
        tokenCount,
        headingPath: currentHeadingPath,
      }),
    });
  }

  // Merge tiny chunks (< 100 tokens) with previous
  const merged: typeof chunks = [];
  for (const chunk of chunks) {
    if (merged.length > 0 && chunk.metadata.tokenCount < 100 && merged[merged.length - 1].metadata.tokenCount < 500) {
      const last = merged[merged.length - 1];
      last.content += "\n\n" + chunk.content;
      last.metadata.tokenCount += chunk.metadata.tokenCount;
      // Keep the more specific chunk type
      if (chunk.metadata.chunkType !== "prose") {
        last.metadata.chunkType = chunk.metadata.chunkType;
      }
    } else {
      merged.push(chunk);
    }
  }

  return merged;
}

/** Extract frontmatter and body from markdown file */
export function parseMarkdownFile(fileContent: string): { frontmatter: Record<string, unknown>; body: string } {
  const fmRegex = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/;
  const match = fileContent.match(fmRegex);

  if (!match) {
    return { frontmatter: {}, body: fileContent };
  }

  try {
    const frontmatter = parseYamlFrontmatter(match[1]);
    return { frontmatter, body: match[2] };
  } catch {
    return { frontmatter: {}, body: fileContent };
  }
}

function parseYamlFrontmatter(yaml: string): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  const lines = yaml.split("\n");
  let currentKey: string | null = null;
  let currentArray: string[] | null = null;

  for (const line of lines) {
    const trimmed = line.trim();

    if (trimmed.startsWith("- ")) {
      // Array item
      if (currentKey && currentArray !== null) {
        currentArray.push(trimmed.slice(2).trim());
      }
      continue;
    }

    const colonIndex = trimmed.indexOf(":");
    if (colonIndex > 0) {
      currentKey = trimmed.slice(0, colonIndex).trim();
      const value = trimmed.slice(colonIndex + 1).trim();

      if (value === "" || value === "|") {
        // Array or multiline string
        currentArray = [];
        result[currentKey] = currentArray;
      } else {
        // Simple value
        currentArray = null;
        result[currentKey] = parseYamlValue(value);
      }
    }
  }

  return result;
}

function parseYamlValue(value: string): unknown {
  // Remove quotes
  value = value.replace(/^["']|["']$/g, "");

  // Boolean
  if (value === "true") return true;
  if (value === "false") return false;

  // Number
  if (/^\d+$/.test(value)) return parseInt(value, 10);
  if (/^\d+\.\d+$/.test(value)) return parseFloat(value);

  return value;
}