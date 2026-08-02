export type ProviderKind = "official_api" | "scraper" | "aggregator";

export type PackageStatus =
  "created" | "in_transit" | "out_for_delivery" | "delivered" | "exception" | "unknown";

export interface User {
  id: string;
  email: string;
  is_admin: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface SetupStatus {
  needs_setup: boolean;
}

export interface Carrier {
  id: string;
  code: string;
  name: string;
  country_code: string;
}

export interface ProviderSetupGuideField {
  key: string;
  label: string;
  type: string;
  required: boolean;
  help_text: string | null;
}

export interface ProviderSetupGuideStep {
  title: string;
  description: string;
  link: string | null;
}

export interface ProviderSetupGuide {
  intro: string;
  steps: ProviderSetupGuideStep[];
  fields: ProviderSetupGuideField[];
}

export interface Provider {
  id: string;
  code: string;
  display_name: string;
  kind: ProviderKind;
  requires_credentials: boolean;
  setup_guide: ProviderSetupGuide | null;
}

export interface ShopCarrierHint {
  carrier: Carrier;
  weight: number;
}

export interface Shop {
  id: string;
  code: string;
  name: string;
  carrier_hints: ShopCarrierHint[];
}

export interface ShopSummary {
  id: string;
  code: string;
  name: string;
}

export interface TrackingEvent {
  id: string;
  occurred_at: string;
  status: PackageStatus;
  location: string | null;
  description: string;
}

export interface Package {
  id: string;
  tracking_number: string;
  label: string | null;
  status: PackageStatus;
  last_checked_at: string | null;
  next_check_at: string | null;
  is_archived: boolean;
  created_at: string;
  carrier: Carrier;
  shop: ShopSummary | null;
  provider: Provider;
  extra_params: Record<string, string> | null;
}

export interface PackageDetail extends Package {
  events: TrackingEvent[];
}

export interface CredentialStatus {
  provider_code: string;
  is_configured: boolean;
}

export interface ApiErrorBody {
  detail?: string | { msg: string }[];
}
