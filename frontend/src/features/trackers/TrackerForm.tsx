import { useQuery } from "@tanstack/react-query";
import { KeyRound, Package, Radio, Store } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import { listCarriers, listProvidersForCarrier } from "@/api/carriers";
import { listShops } from "@/api/shops";
import type { Provider } from "@/api/types";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorBanner, Spinner } from "@/components/Feedback";
import { Field, Input, Select } from "@/components/Input";

const PROVIDER_KIND_LABEL: Record<Provider["kind"], string> = {
  official_api: "API ufficiale del corriere",
  scraper: "Adapter non ufficiale",
  aggregator: "Aggregatore di terze parti",
};

export interface TrackerFormValues {
  shopCode: string;
  carrierCode: string;
  providerCode: string;
  trackingNumber: string;
  label: string;
  destinationPostalCode: string;
}

export const EMPTY_TRACKER_FORM_VALUES: TrackerFormValues = {
  shopCode: "",
  carrierCode: "",
  providerCode: "",
  trackingNumber: "",
  label: "",
  destinationPostalCode: "",
};

interface TrackerFormProps {
  initialValues: TrackerFormValues;
  submitLabel: string;
  isSubmitting: boolean;
  submitError: string | null;
  onSubmit: (values: TrackerFormValues) => void;
}

export function TrackerForm({
  initialValues,
  submitLabel,
  isSubmitting,
  submitError,
  onSubmit,
}: TrackerFormProps) {
  const [shopCode, setShopCode] = useState(initialValues.shopCode);
  const [carrierCode, setCarrierCode] = useState(initialValues.carrierCode);
  const [providerCode, setProviderCode] = useState(initialValues.providerCode);
  const [trackingNumber, setTrackingNumber] = useState(initialValues.trackingNumber);
  const [label, setLabel] = useState(initialValues.label);
  const [destinationPostalCode, setDestinationPostalCode] = useState(
    initialValues.destinationPostalCode,
  );
  const [formError, setFormError] = useState<string | null>(null);

  // initialValues arrives asynchronously in edit mode (the package is fetched first), so seed
  // the form fields once it's actually available instead of only at first render.
  useEffect(() => {
    setShopCode(initialValues.shopCode);
    setCarrierCode(initialValues.carrierCode);
    setProviderCode(initialValues.providerCode);
    setTrackingNumber(initialValues.trackingNumber);
    setLabel(initialValues.label);
    setDestinationPostalCode(initialValues.destinationPostalCode);
  }, [
    initialValues.shopCode,
    initialValues.carrierCode,
    initialValues.providerCode,
    initialValues.trackingNumber,
    initialValues.label,
    initialValues.destinationPostalCode,
  ]);

  const shopsQuery = useQuery({ queryKey: ["shops"], queryFn: listShops });
  const carriersQuery = useQuery({ queryKey: ["carriers"], queryFn: listCarriers });

  const suggestedCarrierCodes = useMemo(() => {
    if (!shopCode || !shopsQuery.data) return [];
    const shop = shopsQuery.data.find((s) => s.code === shopCode);
    return shop?.carrier_hints.map((hint) => hint.carrier.code) ?? [];
  }, [shopCode, shopsQuery.data]);

  const providersQuery = useQuery({
    queryKey: ["carrier-providers", carrierCode],
    queryFn: () => listProvidersForCarrier(carrierCode),
    enabled: Boolean(carrierCode),
  });

  const selectedProvider = providersQuery.data?.find((p) => p.code === providerCode);
  const showPostalCodeField = selectedProvider?.kind === "aggregator";

  const handleCarrierChange = (code: string) => {
    setCarrierCode(code);
    setProviderCode("");
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    setFormError(null);
    if (!carrierCode || !providerCode || !trackingNumber) {
      setFormError("Compila corriere, metodo di tracciamento e codice di spedizione.");
      return;
    }
    onSubmit({
      shopCode,
      carrierCode,
      providerCode,
      trackingNumber: trackingNumber.trim(),
      label: label.trim(),
      destinationPostalCode: destinationPostalCode.trim(),
    });
  };

  const sortedCarriers = useMemo(() => {
    const carriers = carriersQuery.data ?? [];
    if (suggestedCarrierCodes.length === 0) return carriers;
    return [...carriers].sort((a, b) => {
      const aRank = suggestedCarrierCodes.indexOf(a.code);
      const bRank = suggestedCarrierCodes.indexOf(b.code);
      if (aRank === -1 && bRank === -1) return a.name.localeCompare(b.name);
      if (aRank === -1) return 1;
      if (bRank === -1) return -1;
      return aRank - bRank;
    });
  }, [carriersQuery.data, suggestedCarrierCodes]);

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
          <Store className="size-4" aria-hidden="true" />
          1. Dove hai acquistato? (opzionale)
        </div>
        <Field label="Negozio" htmlFor="shop">
          <Select
            id="shop"
            value={shopCode}
            onChange={(e) => setShopCode(e.target.value)}
            disabled={shopsQuery.isLoading}
          >
            <option value="">Non specificato</option>
            {shopsQuery.data?.map((shop) => (
              <option key={shop.code} value={shop.code}>
                {shop.name}
              </option>
            ))}
          </Select>
        </Field>
      </Card>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
          <Package className="size-4" aria-hidden="true" />
          2. Chi spedisce?
        </div>
        <Field label="Corriere" htmlFor="carrier">
          <Select
            id="carrier"
            value={carrierCode}
            onChange={(e) => handleCarrierChange(e.target.value)}
            disabled={carriersQuery.isLoading}
            required
          >
            <option value="">Seleziona un corriere</option>
            {sortedCarriers.map((carrier) => (
              <option key={carrier.code} value={carrier.code}>
                {carrier.name}
                {suggestedCarrierCodes.includes(carrier.code) ? " (suggerito)" : ""}
              </option>
            ))}
          </Select>
        </Field>
      </Card>

      {carrierCode && (
        <Card className="flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
            <Radio className="size-4" aria-hidden="true" />
            3. Come vuoi tracciarlo?
          </div>
          {providersQuery.isLoading && <Spinner label="Ricerca metodi disponibili..." />}
          {providersQuery.data && providersQuery.data.length === 0 && (
            <ErrorBanner message="Nessun metodo di tracciamento disponibile per questo corriere." />
          )}
          <div className="flex flex-col gap-2">
            {providersQuery.data?.map((provider) => (
              <label
                key={provider.code}
                className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                  providerCode === provider.code
                    ? "border-brand-500 bg-brand-50 dark:bg-brand-900/40"
                    : "border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                }`}
              >
                <input
                  type="radio"
                  name="provider"
                  value={provider.code}
                  checked={providerCode === provider.code}
                  onChange={() => setProviderCode(provider.code)}
                  className="mt-1"
                />
                <div className="flex flex-col">
                  <span className="font-medium text-slate-900 dark:text-slate-100">
                    {provider.display_name}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {PROVIDER_KIND_LABEL[provider.kind]}
                  </span>
                  {provider.requires_credentials && (
                    <span className="mt-1 flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
                      <KeyRound className="size-3" aria-hidden="true" />
                      Richiede una connessione configurata in Impostazioni &rarr; Connessioni
                    </span>
                  )}
                </div>
              </label>
            ))}
          </div>
        </Card>
      )}

      <Card className="flex flex-col gap-4">
        <div className="text-sm font-semibold text-slate-700 dark:text-slate-200">
          4. Dettagli spedizione
        </div>
        <Field label="Codice di spedizione" htmlFor="tracking-number">
          <Input
            id="tracking-number"
            required
            value={trackingNumber}
            onChange={(e) => setTrackingNumber(e.target.value)}
            placeholder="es. 60011234567890123456789012"
          />
        </Field>
        <Field label="Etichetta (opzionale)" htmlFor="label">
          <Input
            id="label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="es. Tastiera meccanica"
          />
        </Field>
        {showPostalCodeField && (
          <Field
            label="Codice postale destinatario"
            htmlFor="destination-postal-code"
            helpText="Richiesto da 17TRACK per alcuni corrieri di questo tipo (es. Mondial Relay)."
          >
            <Input
              id="destination-postal-code"
              value={destinationPostalCode}
              onChange={(e) => setDestinationPostalCode(e.target.value)}
              placeholder="es. 20100"
            />
          </Field>
        )}
      </Card>

      {(formError ?? submitError) && <ErrorBanner message={formError ?? submitError ?? ""} />}

      <Button type="submit" isLoading={isSubmitting} className="self-start">
        {submitLabel}
      </Button>
    </form>
  );
}
