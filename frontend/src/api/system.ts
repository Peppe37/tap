import { apiFetch } from "./client";
import type { UpdateStatus } from "./types";

export function getUpdateStatus(): Promise<UpdateStatus> {
  return apiFetch<UpdateStatus>("/system/update-status");
}
