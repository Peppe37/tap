import { useQuery } from "@tanstack/react-query";
import { PackageSearch, Plus } from "lucide-react";
import { Link } from "react-router-dom";

import { listPackages } from "@/api/packages";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorBanner, Spinner } from "@/components/Feedback";
import { StatusPill } from "@/components/StatusPill";
import { formatRelativeTime } from "@/lib/format";

export function TrackerList() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["packages"],
    queryFn: () => listPackages(),
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">I tuoi pacchi</h1>
        <Link to="/packages/new">
          <Button>
            <Plus className="size-4" aria-hidden="true" />
            Aggiungi tracker
          </Button>
        </Link>
      </div>

      {isLoading && <Spinner label="Caricamento pacchi..." />}
      {isError && <ErrorBanner message="Impossibile caricare i pacchi." />}

      {data && data.length === 0 && (
        <Card className="flex flex-col items-center gap-3 py-16 text-center">
          <PackageSearch className="size-10 text-slate-400" aria-hidden="true" />
          <p className="text-slate-600 dark:text-slate-300">
            Non stai ancora tracciando nessun pacco.
          </p>
          <Link to="/packages/new">
            <Button>
              <Plus className="size-4" aria-hidden="true" />
              Aggiungi il primo tracker
            </Button>
          </Link>
        </Card>
      )}

      {data && data.length > 0 && (
        <div className="flex flex-col gap-3">
          {data.map((pkg) => (
            <Link key={pkg.id} to={`/packages/${pkg.id}`}>
              <Card className="flex items-center justify-between gap-4 transition-shadow hover:shadow-md">
                <div className="flex flex-col gap-1">
                  <span className="font-medium text-slate-900 dark:text-slate-100">
                    {pkg.label ?? pkg.tracking_number}
                  </span>
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    {pkg.carrier.name} &middot; {pkg.provider.display_name}
                    {pkg.shop && <> &middot; {pkg.shop.name}</>}
                  </span>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <StatusPill status={pkg.status} />
                  {pkg.last_checked_at && (
                    <span className="text-xs text-slate-400">
                      aggiornato {formatRelativeTime(pkg.last_checked_at)}
                    </span>
                  )}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
