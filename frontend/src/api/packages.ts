import { apiFetch } from "./client";
import type { Package, PackageDetail } from "./types";

export interface CreatePackageInput {
  tracking_number: string;
  carrier_code: string;
  provider_code: string;
  shop_code?: string;
  label?: string;
  extra_params?: Record<string, string>;
}

export interface UpdatePackageInput {
  label?: string;
  is_archived?: boolean;
  tracking_number?: string;
  carrier_code?: string;
  provider_code?: string;
  shop_code?: string | null;
  extra_params?: Record<string, string> | null;
}

export function listPackages(includeArchived = false): Promise<Package[]> {
  const query = includeArchived ? "?include_archived=true" : "";
  return apiFetch<Package[]>(`/packages${query}`);
}

export function getPackage(id: string): Promise<PackageDetail> {
  return apiFetch<PackageDetail>(`/packages/${encodeURIComponent(id)}`);
}

export function createPackage(input: CreatePackageInput): Promise<PackageDetail> {
  return apiFetch<PackageDetail>("/packages", { method: "POST", body: input });
}

export function updatePackage(id: string, input: UpdatePackageInput): Promise<PackageDetail> {
  return apiFetch<PackageDetail>(`/packages/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: input,
  });
}

export function deletePackage(id: string): Promise<void> {
  return apiFetch<void>(`/packages/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function refreshPackage(id: string): Promise<PackageDetail> {
  return apiFetch<PackageDetail>(`/packages/${encodeURIComponent(id)}/refresh`, {
    method: "POST",
  });
}
