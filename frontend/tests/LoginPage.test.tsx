import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "@/features/auth/LoginPage";

const loginMock = vi.fn();

vi.mock("@/auth/AuthContext", () => ({
  useAuth: () => ({ login: loginMock }),
}));

describe("LoginPage", () => {
  it("submits the entered credentials", async () => {
    loginMock.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email"), "admin@example.com");
    await user.type(screen.getByLabelText("Password"), "correct-horse-battery");
    await user.click(screen.getByRole("button", { name: "Accedi" }));

    expect(loginMock).toHaveBeenCalledWith("admin@example.com", "correct-horse-battery");
  });

  it("shows an error banner when login fails", async () => {
    loginMock.mockRejectedValueOnce(new Error("nope"));
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email"), "admin@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Accedi" }));

    expect(await screen.findByText("Email o password non corrette.")).toBeInTheDocument();
  });
});
