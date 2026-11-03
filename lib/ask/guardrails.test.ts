import { describe, expect, it } from "vitest";
import { checkInput, clean, failureLimit, GLOBAL_DAILY, IP_DAILY, ipHash, matchesSecret, normalise, usageLimit } from "./guardrails";

describe("clean", () => {
  it("turns tab, CR and LF into spaces and strips other control characters", () => {
    expect(clean("  When\tcan\r\nthey\u0000 drill\u0007?\u007f ")).toBe("When can  they drill?");
  });
});

describe("normalise", () => {
  it("lowercases, trims and collapses whitespace", () => {
    expect(normalise("  How LATE can\n\nmy neighbour   run a leaf blower? ")).toBe("how late can my neighbour run a leaf blower?");
  });

  it("gives the same key for questions that differ only in case, spacing and control characters", () => {
    expect(normalise("What is § 591-2.1?")).toBe(normalise(" what\u0000 is  §  591-2.1? "));
  });
});

describe("checkInput", () => {
  it("allows 300 characters and stops at 301", () => {
    expect(checkInput("a".repeat(299))).toBe("ok");
    expect(checkInput("a".repeat(300))).toBe("ok");
    expect(checkInput("a".repeat(301))).toBe("too_long");
  });

  it("counts after control characters are stripped", () => {
    expect(checkInput(clean("a".repeat(300) + "\u0000\u0001"))).toBe("ok");
  });
});

describe("ipHash", () => {
  it("is stable per salt, differs across salts, and never contains the IP", () => {
    const h = ipHash("203.0.113.7", "salt-a");
    expect(h).toBe(ipHash("203.0.113.7", "salt-a"));
    expect(h).not.toBe(ipHash("203.0.113.7", "salt-b"));
    expect(h).not.toBe(ipHash("203.0.113.8", "salt-a"));
    expect(h).toMatch(/^[0-9a-f]{64}$/);
  });
});

describe("matchesSecret", () => {
  const SECRET = "s3cret-value";

  it("accepts only the exact secret", () => {
    expect(matchesSecret(SECRET, SECRET)).toBe(true);
    expect(matchesSecret("s3cret-valu", SECRET)).toBe(false);
    expect(matchesSecret(null, SECRET)).toBe(false);
  });

  it("grants nothing when no secret is configured", () => {
    expect(matchesSecret("", "")).toBe(false);
    expect(matchesSecret("anything", undefined)).toBe(false);
  });
});

describe("usageLimit", () => {
  it("allows 30 questions per IP and 30 in all per day", () => {
    expect([IP_DAILY, GLOBAL_DAILY]).toEqual([30, 30]);
  });

  // counts are questions already asked today, before this one
  it.each([
    [29, null],
    [30, "ip_daily"],
    [31, "ip_daily"],
  ])("per IP: %i before → %s", (ip, limit) => {
    expect(usageLimit({ ip, global: 0 })).toBe(limit);
  });

  it.each([
    [29, null],
    [30, "global_daily"],
    [31, "global_daily"],
  ])("globally: %i before → %s", (global, limit) => {
    expect(usageLimit({ ip: 0, global })).toBe(limit);
  });

  it("names the visitor's own limit when both are reached", () => {
    expect(usageLimit({ ip: 30, global: 30 })).toBe("ip_daily");
  });
});

describe("failureLimit", () => {
  const status = (statusCode: number) => Object.assign(new Error(), { statusCode });

  it("maps out-of-credit to budget and rate-limited to burst", () => {
    expect(failureLimit(status(402))).toBe("budget");
    expect(failureLimit(status(429))).toBe("burst");
  });

  it("finds the status behind retry and cause wrappers", () => {
    expect(failureLimit({ lastError: status(429) })).toBe("burst");
    expect(failureLimit(new Error("wrapped", { cause: status(402) }))).toBe("budget");
  });

  it("maps everything else to unavailable", () => {
    expect(failureLimit(status(500))).toBe("unavailable");
    expect(failureLimit(new Error("connection refused"))).toBe("unavailable");
    expect(failureLimit(undefined)).toBe("unavailable");
  });
});
