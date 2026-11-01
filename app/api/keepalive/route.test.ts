import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SearchRow } from "@/lib/ask/types";
import query from "./query.json";

const search = vi.fn(async (_question: string, _embedding: number[], _mode: string): Promise<SearchRow[]> => []);
const embed = vi.fn();

vi.mock("@/lib/ask/deps", () => ({ createDeps: () => ({ search, embed }) }));

const { GET } = await import("./route");

const SECRET = "cron-s3cret";
const get = (headers: Record<string, string> = {}) => GET(new Request("http://test/api/keepalive", { headers }));

describe("GET /api/keepalive", () => {
  beforeEach(() => {
    vi.stubEnv("CRON_SECRET", SECRET);
    search.mockClear();
  });

  it("returns 401 and touches nothing without the cron secret", async () => {
    expect((await get()).status).toBe(401);
    expect((await get({ authorization: "Bearer wrong" })).status).toBe(401);
    expect((await get({ authorization: SECRET })).status).toBe(401);
    expect(search).not.toHaveBeenCalled();
  });

  it("returns 401 when CRON_SECRET is unset, even for an empty bearer", async () => {
    vi.stubEnv("CRON_SECRET", "");
    expect((await get({ authorization: "Bearer " })).status).toBe(401);
    expect(search).not.toHaveBeenCalled();
  });

  it("with the secret, runs the real search with the stored embedding and never embeds", async () => {
    search.mockResolvedValueOnce([{} as SearchRow, {} as SearchRow]);
    const res = await get({ authorization: `Bearer ${SECRET}` });
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, rows: 2 });
    expect(search).toHaveBeenCalledWith(query.question, query.embedding, "hybrid");
    expect(embed).not.toHaveBeenCalled();
  });

  it("returns 500 when the search fails", async () => {
    search.mockRejectedValueOnce(new Error("search_chunks: down"));
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect((await get({ authorization: `Bearer ${SECRET}` })).status).toBe(500);
  });

  it("stores a full-size query embedding", () => {
    expect(query.embedding).toHaveLength(1024);
  });
});
