import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { UpdateStatus } from "@/api/types";
import { UpdateBanner } from "@/features/system/UpdateBanner";

const getUpdateStatusMock = vi.fn<() => Promise<UpdateStatus>>();
const useAuthMock = vi.fn<() => { user: { is_admin: boolean } | null }>();

vi.mock("@/api/system", () => ({
  getUpdateStatus: () => getUpdateStatusMock(),
}));

vi.mock("@/auth/AuthContext", () => ({
  useAuth: () => useAuthMock(),
}));

function renderBanner() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <UpdateBanner />
    </QueryClientProvider>,
  );
}

describe("UpdateBanner", () => {
  beforeEach(() => {
    getUpdateStatusMock.mockReset();
    useAuthMock.mockReset();
  });

  it("renders nothing for a non-admin user", async () => {
    useAuthMock.mockReturnValue({ user: { is_admin: false } });
    getUpdateStatusMock.mockResolvedValue({
      current_version: "0.1.0",
      latest_version: "v0.2.0",
      update_available: true,
      release_url: "https://github.com/Peppe37/tap/releases/tag/v0.2.0",
    });

    renderBanner();

    await waitFor(() => expect(getUpdateStatusMock).not.toHaveBeenCalled());
    expect(screen.queryByText(/Nuova versione disponibile/)).not.toBeInTheDocument();
  });

  it("renders nothing when already up to date", async () => {
    useAuthMock.mockReturnValue({ user: { is_admin: true } });
    getUpdateStatusMock.mockResolvedValue({
      current_version: "0.2.0",
      latest_version: "v0.2.0",
      update_available: false,
      release_url: null,
    });

    renderBanner();

    await waitFor(() => expect(getUpdateStatusMock).toHaveBeenCalled());
    expect(screen.queryByText(/Nuova versione disponibile/)).not.toBeInTheDocument();
  });

  it("shows the banner with a link to the release when an update is available", async () => {
    useAuthMock.mockReturnValue({ user: { is_admin: true } });
    getUpdateStatusMock.mockResolvedValue({
      current_version: "0.1.0",
      latest_version: "v0.2.0",
      update_available: true,
      release_url: "https://github.com/Peppe37/tap/releases/tag/v0.2.0",
    });

    renderBanner();

    expect(await screen.findByText(/Nuova versione disponibile/)).toBeInTheDocument();
    expect(screen.getByText("v0.2.0")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Vedi le novità" })).toHaveAttribute(
      "href",
      "https://github.com/Peppe37/tap/releases/tag/v0.2.0",
    );
  });

  it("hides the banner after dismissal and remembers it for that version", async () => {
    useAuthMock.mockReturnValue({ user: { is_admin: true } });
    getUpdateStatusMock.mockResolvedValue({
      current_version: "0.1.0",
      latest_version: "v0.2.0",
      update_available: true,
      release_url: "https://github.com/Peppe37/tap/releases/tag/v0.2.0",
    });
    const user = userEvent.setup();

    renderBanner();
    await screen.findByText(/Nuova versione disponibile/);
    await user.click(screen.getByRole("button", { name: "Nascondi avviso" }));

    expect(screen.queryByText(/Nuova versione disponibile/)).not.toBeInTheDocument();
    expect(localStorage.getItem("tap.dismissed_update_version")).toBe("v0.2.0");
  });
});
