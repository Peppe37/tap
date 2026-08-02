import { apiFetch } from "./client";
import type { Shop } from "./types";

export function listShops(): Promise<Shop[]> {
  return apiFetch<Shop[]>("/shops");
}
