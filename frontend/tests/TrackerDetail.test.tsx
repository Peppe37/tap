import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { UpdatePackageInput } from "@/api/packages";
import type { PackageDetail } from "@/api/types";
import { TrackerDetail } from "@/features/trackers/TrackerDetail";

const getPackageMock = vi.fn<(id: string) => Promise<PackageDetail>>();
const updatePackageMock = vi.fn<(id: string, input: UpdatePackageInput) => Promise<unknown>>();

vi.mock("@/api/packages", () => ({
  getPackage: (id: string) => getPackageMock(id),
  updatePackage: (id: string, input: UpdatePackageInput) => updatePackageMock(id, input),
  refreshPackage: vi.fn(),
  deletePackage: vi.fn(),
}));

function buildPackage(overrides: Partial<PackageDetail> = {}): PackageDetail {
  return {
    id: "pkg-1",
    tracking_number: "58438531",
    label: null,
    status: "created",
    last_checked_at: null,
    next_check_at: null,
    is_archived: false,
    created_at: "2026-07-01T00:00:00Z",
    extra_params: null,
    carrier: { id: "c1", code: "mondial_relay", name: "Mondial Relay", country_code: "FR" },
    shop: { id: "s1", code: "vinted", name: "Vinted" },
    provider: {
      id: "p1",
      code: "aggregator_17track",
      display_name: "17TRACK",
      kind: "aggregator",
      requires_credentials: true,
      setup_guide: null,
    },
    events: [],
    ...overrides,
  };
}

function renderDetail(pkg: PackageDetail) {
  getPackageMock.mockResolvedValue(pkg);
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/packages/${pkg.id}`]}>
        <Routes>
          <Route path="/packages/:id" element={<TrackerDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("TrackerDetail rename", () => {
  beforeEach(() => {
    getPackageMock.mockReset();
    updatePackageMock.mockReset();
  });

  it("shows the tracking number as the title when no label is set", async () => {
    renderDetail(buildPackage());

    expect(await screen.findByRole("heading", { name: "58438531" })).toBeInTheDocument();
  });

  it("lets the user rename the tracker and persists the new label", async () => {
    const pkg = buildPackage({ label: "Vecchio nome" });
    renderDetail(pkg);
    updatePackageMock.mockResolvedValue({ ...pkg, label: "Scarpe da running" });
    const user = userEvent.setup();

    await screen.findByRole("heading", { name: "Vecchio nome" });
    await user.click(screen.getByRole("button", { name: "Rinomina tracker" }));

    const input = screen.getByPlaceholderText("Nome del tracker");
    await user.clear(input);
    await user.type(input, "Scarpe da running");
    await user.click(screen.getByRole("button", { name: "Salva nome" }));

    await waitFor(() => {
      expect(updatePackageMock).toHaveBeenCalledWith("pkg-1", { label: "Scarpe da running" });
    });
  });

  it("discards the draft when the user cancels", async () => {
    const pkg = buildPackage({ label: "Nome originale" });
    renderDetail(pkg);
    const user = userEvent.setup();

    await screen.findByRole("heading", { name: "Nome originale" });
    await user.click(screen.getByRole("button", { name: "Rinomina tracker" }));
    const input = screen.getByPlaceholderText("Nome del tracker");
    await user.clear(input);
    await user.type(input, "Qualcosa che non salverò");
    await user.click(screen.getByRole("button", { name: "Annulla" }));

    expect(screen.getByRole("heading", { name: "Nome originale" })).toBeInTheDocument();
    expect(updatePackageMock).not.toHaveBeenCalled();
  });

  it("does not allow saving an empty name", async () => {
    renderDetail(buildPackage({ label: "Nome originale" }));
    const user = userEvent.setup();

    await screen.findByRole("heading", { name: "Nome originale" });
    await user.click(screen.getByRole("button", { name: "Rinomina tracker" }));
    const input = screen.getByPlaceholderText("Nome del tracker");
    await user.clear(input);

    expect(screen.getByRole("button", { name: "Salva nome" })).toBeDisabled();
  });
});
