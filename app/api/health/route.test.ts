import { describe, expect, it, vi } from "vitest";

const pingDb = vi.fn(async () => {});

vi.mock("@/lib/ask/deps", () => ({ pingDb }));

const { GET } = await import("./route");

describe("GET /api/health", () => {
  it("returns 200 when the DB answers", async () => {
    const res = await GET();
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true });
  });

  it("returns 503 when the DB is unreachable, so the workflow's curl fails", async () => {
    pingDb.mockRejectedValueOnce(new Error("reading snapshot: fetch failed"));
    vi.spyOn(console, "error").mockImplementation(() => {});
    const res = await GET();
    expect(res.status).toBe(503);
    expect(await res.json()).toEqual({ ok: false });
  });
});
