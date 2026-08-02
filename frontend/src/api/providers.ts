import { apiFetch } from "./client";
import type { CredentialStatus, Provider } from "./types";

export function listProviders(): Promise<Provider[]> {
  return apiFetch<Provider[]>("/providers");
}

export function getCredentialStatus(providerCode: string): Promise<CredentialStatus> {
  return apiFetch<CredentialStatus>(
    `/providers/${encodeURIComponent(providerCode)}/credential-status`,
  );
}

export function testCredential(
  providerCode: string,
  fields: Record<string, string>,
): Promise<{ is_valid: boolean }> {
  return apiFetch<{ is_valid: boolean }>(
    `/providers/${encodeURIComponent(providerCode)}/test-credential`,
    { method: "POST", body: { fields } },
  );
}

export function saveCredential(
  providerCode: string,
  fields: Record<string, string>,
): Promise<void> {
  return apiFetch<void>(`/providers/${encodeURIComponent(providerCode)}/credential`, {
    method: "PUT",
    body: { fields },
  });
}

export function deleteCredential(providerCode: string): Promise<void> {
  return apiFetch<void>(`/providers/${encodeURIComponent(providerCode)}/credential`, {
    method: "DELETE",
  });
}
