import { apiFetch } from "./client";
import type { Carrier, Provider } from "./types";

export function listCarriers(): Promise<Carrier[]> {
  return apiFetch<Carrier[]>("/carriers");
}

export function listProvidersForCarrier(carrierCode: string): Promise<Provider[]> {
  return apiFetch<Provider[]>(`/carriers/${encodeURIComponent(carrierCode)}/providers`);
}
