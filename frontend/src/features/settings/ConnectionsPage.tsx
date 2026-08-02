import { useQuery } from "@tanstack/react-query";

import { listProviders } from "@/api/providers";
import { ErrorBanner, Spinner } from "@/components/Feedback";

import { ConnectionGuideCard } from "./ConnectionGuideCard";

export function ConnectionsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["providers"],
    queryFn: listProviders,
  });

  const providersRequiringCredentials = data?.filter((provider) => provider.requires_credentials);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Connessioni</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Alcuni metodi di tracciamento richiedono una tua chiave personale per essere usati.
          Configurali qui una volta e saranno disponibili per tutti i tuoi tracker.
        </p>
      </div>

      {isLoading && <Spinner label="Caricamento connessioni..." />}
      {isError && <ErrorBanner message="Impossibile caricare i provider." />}

      {providersRequiringCredentials?.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Nessun provider richiede al momento una connessione personale.
        </p>
      )}

      <div className="flex flex-col gap-4">
        {providersRequiringCredentials?.map((provider) => (
          <ConnectionGuideCard key={provider.code} provider={provider} />
        ))}
      </div>
    </div>
  );
}
