import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "@/api/client";
import { getPackage, updatePackage } from "@/api/packages";
import { ErrorBanner, InfoBanner, Spinner } from "@/components/Feedback";

import { TrackerForm } from "./TrackerForm";
import type { TrackerFormValues } from "./TrackerForm";

export function EditTrackerPage() {
  const { id } = useParams<{ id: string }>();
  const packageId = id ?? "";
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { data: pkg, isLoading } = useQuery({
    queryKey: ["package", packageId],
    queryFn: () => getPackage(packageId),
    enabled: Boolean(packageId),
  });

  const updateMutation = useMutation({
    mutationFn: (values: TrackerFormValues) =>
      updatePackage(packageId, {
        tracking_number: values.trackingNumber,
        carrier_code: values.carrierCode,
        provider_code: values.providerCode,
        shop_code: values.shopCode || null,
        label: values.label || undefined,
        extra_params: values.destinationPostalCode
          ? { destination_postal_code: values.destinationPostalCode }
          : null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["package", packageId] });
      void queryClient.invalidateQueries({ queryKey: ["packages"] });
      void navigate(`/packages/${packageId}`);
    },
    onError: (err: unknown) => {
      setSubmitError(err instanceof ApiError ? err.message : "Impossibile salvare le modifiche.");
    },
  });

  if (isLoading) return <Spinner label="Caricamento pacco..." />;
  if (!pkg) return <ErrorBanner message="Pacco non trovato." />;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Link
        to={`/packages/${packageId}`}
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Torna al pacco
      </Link>
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
        Modifica tracker
      </h1>
      <InfoBanner message="Cambiare corriere, metodo o codice di spedizione azzera la cronologia e lo stato attuali: verranno recuperati al prossimo aggiornamento." />
      <TrackerForm
        initialValues={{
          shopCode: pkg.shop?.code ?? "",
          carrierCode: pkg.carrier.code,
          providerCode: pkg.provider.code,
          trackingNumber: pkg.tracking_number,
          label: pkg.label ?? "",
          destinationPostalCode: pkg.extra_params?.destination_postal_code ?? "",
        }}
        submitLabel="Salva modifiche"
        isSubmitting={updateMutation.isPending}
        submitError={submitError}
        onSubmit={(values) => updateMutation.mutate(values)}
      />
    </div>
  );
}
