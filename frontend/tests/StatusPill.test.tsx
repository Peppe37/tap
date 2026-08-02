import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusPill } from "@/components/StatusPill";

describe("StatusPill", () => {
  it("renders the Italian label for each known status", () => {
    render(<StatusPill status="delivered" />);
    expect(screen.getByText("Consegnato")).toBeInTheDocument();
  });

  it("renders a distinct label for out_for_delivery", () => {
    render(<StatusPill status="out_for_delivery" />);
    expect(screen.getByText("In consegna")).toBeInTheDocument();
  });
});
