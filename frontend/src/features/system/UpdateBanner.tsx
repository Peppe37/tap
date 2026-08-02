import { useQuery } from "@tanstack/react-query";
import { ArrowUpCircle, X } from "lucide-react";
import { useState } from "react";

import { getUpdateStatus } from "@/api/system";
import { useAuth } from "@/auth/AuthContext";

const DISMISSED_VERSION_KEY = "tap.dismissed_update_version";
const CHECK_INTERVAL_MS = 60 * 60 * 1000;

export function UpdateBanner() {
  const { user } = useAuth();
  const [dismissedVersion, setDismissedVersion] = useState(() =>
    localStorage.getItem(DISMISSED_VERSION_KEY),
  );

  const query = useQuery({
    queryKey: ["update-status"],
    queryFn: getUpdateStatus,
    enabled: Boolean(user?.is_admin),
    staleTime: CHECK_INTERVAL_MS,
    refetchInterval: CHECK_INTERVAL_MS,
    retry: false,
  });

  const status = query.data;
  if (!status?.update_available || status.latest_version === dismissedVersion) {
    return null;
  }

  const dismiss = () => {
    localStorage.setItem(DISMISSED_VERSION_KEY, status.latest_version);
    setDismissedVersion(status.latest_version);
  };

  return (
    <div className="mb-6 flex items-start justify-between gap-3 rounded-lg border border-brand-200 bg-brand-50 px-3 py-2 text-sm text-brand-800 dark:border-brand-900 dark:bg-brand-950 dark:text-brand-200">
      <div className="flex items-start gap-2">
        <ArrowUpCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <span>
          Nuova versione disponibile: <strong>{status.latest_version}</strong> (stai usando{" "}
          {status.current_version}).{" "}
          {status.release_url && (
            <a
              href={status.release_url}
              target="_blank"
              rel="noreferrer"
              className="font-medium underline underline-offset-2"
            >
              Vedi le novità
            </a>
          )}
        </span>
      </div>
      <button
        onClick={dismiss}
        aria-label="Nascondi avviso"
        className="shrink-0 text-brand-600 hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-200"
      >
        <X className="size-4" aria-hidden="true" />
      </button>
    </div>
  );
}
