import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch, AuthenticationRequiredError } from "@/api/client";
import { getAccessToken, setTokens } from "@/auth/tokenStorage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiFetch", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed JSON and attaches the bearer token when authenticated", async () => {
    setTokens("access-1", "refresh-1");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiFetch<{ ok: boolean }>("/health");

    expect(result).toEqual({ ok: true });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer access-1");
  });

  it("throws ApiError with the server-provided detail on failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: "Invalid email or password" }, 401));
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch("/auth/login", { authenticated: false })).rejects.toMatchObject({
      status: 401,
      message: "Invalid email or password",
    });
  });

  it("retries once after a successful token refresh on 401", async () => {
    setTokens("expired-access", "valid-refresh");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "Invalid or expired token" }, 401))
      .mockResolvedValueOnce(
        jsonResponse({ access_token: "new-access", refresh_token: "new-refresh" }),
      )
      .mockResolvedValueOnce(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiFetch<{ ok: boolean }>("/packages");

    expect(result).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(getAccessToken()).toBe("new-access");
  });

  it("clears tokens and raises AuthenticationRequiredError when refresh also fails", async () => {
    setTokens("expired-access", "expired-refresh");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: "Invalid or expired token" }, 401))
      .mockResolvedValueOnce(jsonResponse({ detail: "Invalid or expired refresh token" }, 401));
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch("/packages")).rejects.toBeInstanceOf(AuthenticationRequiredError);
    expect(getAccessToken()).toBeNull();
  });
});
