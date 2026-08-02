import { apiFetch } from "./client";
import type { SetupStatus, TokenPair, User } from "./types";

export function getSetupStatus(): Promise<SetupStatus> {
  return apiFetch<SetupStatus>("/auth/setup-status", { authenticated: false });
}

export function setupAdmin(email: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/auth/setup", {
    method: "POST",
    body: { email, password },
    authenticated: false,
  });
}

export function login(email: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>("/auth/login", {
    method: "POST",
    body: { email, password },
    authenticated: false,
  });
}

export function getCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function createUser(email: string, password: string, isAdmin: boolean): Promise<User> {
  return apiFetch<User>("/auth/users", {
    method: "POST",
    body: { email, password, is_admin: isAdmin },
  });
}

export function listUsers(): Promise<User[]> {
  return apiFetch<User[]>("/auth/users");
}
