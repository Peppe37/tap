import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "@/api/client";
import { createPackage } from "@/api/packages";

import { EMPTY_TRACKER_FORM_VALUES, TrackerForm } from "./TrackerForm";
import type { TrackerFormValues } from "./TrackerForm";

export function AddTrackerWizard() {
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (values: TrackerFormValues) =>
      createPackage({
        tracking_number: values.trackingNumber,
        carrier_code: values.carrierCode,
        provider_code: values.providerCode,
        shop_code: values.shopCode || undefined,
        label: values.label || undefined,
        extra_params: values.destinationPostalCode
          ? { destination_postal_code: values.destinationPostalCode }
          : undefined,
      }),
    onSuccess: (created) => void navigate(`/packages/${created.id}`),
    onError: (err: unknown) => {
      setSubmitError(err instanceof ApiError ? err.message : "Impossibile creare il tracker.");
    },
  });

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
        Aggiungi un tracker
      </h1>
      <TrackerForm
        initialValues={EMPTY_TRACKER_FORM_VALUES}
        submitLabel="Crea tracker"
        isSubmitting={createMutation.isPending}
        submitError={submitError}
        onSubmit={(values) => createMutation.mutate(values)}
      />
    </div>
  );
}
