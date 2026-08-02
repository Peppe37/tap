import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Archive,
  ArchiveRestore,
  ArrowLeft,
  Check,
  Pencil,
  RefreshCw,
  SlidersHorizontal,
  Trash2,
  X,
} from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { deletePackage, getPackage, refreshPackage, updatePackage } from "@/api/packages";
import { ApiError } from "@/api/client";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorBanner, Spinner } from "@/components/Feedback";
import { Input } from "@/components/Input";
import { StatusPill } from "@/components/StatusPill";
import { formatDateTime } from "@/lib/format";

import { Timeline } from "./Timeline";

export function TrackerDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [labelDraft, setLabelDraft] = useState("");

  const packageId = id ?? "";
  const { data: pkg, isLoading } = useQuery({
    queryKey: ["package", packageId],
    queryFn: () => getPackage(packageId),
    enabled: Boolean(packageId),
  });

  const refreshMutation = useMutation({
    mutationFn: () => refreshPackage(packageId),
    onSuccess: (updated) => {
      setRefreshError(null);
      queryClient.setQueryData(["package", packageId], updated);
      void queryClient.invalidateQueries({ queryKey: ["packages"] });
    },
    onError: (err: unknown) => {
      setRefreshError(
        err instanceof ApiError ? err.message : "Impossibile aggiornare il tracciamento.",
      );
    },
  });

  const renameMutation = useMutation({
    mutationFn: (label: string) => updatePackage(packageId, { label }),
    onSuccess: () => {
      setIsEditingLabel(false);
      void queryClient.invalidateQueries({ queryKey: ["package", packageId] });
      void queryClient.invalidateQueries({ queryKey: ["packages"] });
    },
  });

  const archiveMutation = useMutation({
    mutationFn: () => updatePackage(packageId, { is_archived: !pkg?.is_archived }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["package", packageId] });
      void queryClient.invalidateQueries({ queryKey: ["packages"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deletePackage(packageId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["packages"] });
      void navigate("/");
    },
  });

  if (isLoading) return <Spinner label="Caricamento pacco..." />;
  if (!pkg) return <ErrorBanner message="Pacco non trovato." />;

  return (
    <div className="flex flex-col gap-6">
      <Link
        to="/"
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Torna ai pacchi
      </Link>

      <Card className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            {isEditingLabel ? (
              <form
                className="flex items-center gap-2"
                onSubmit={(event: FormEvent) => {
                  event.preventDefault();
                  const trimmed = labelDraft.trim();
                  if (trimmed) renameMutation.mutate(trimmed);
                }}
              >
                <Input
                  autoFocus
                  value={labelDraft}
                  onChange={(e) => setLabelDraft(e.target.value)}
                  placeholder="Nome del tracker"
                  className="text-xl font-semibold"
                />
                <Button
                  type="submit"
                  variant="ghost"
                  isLoading={renameMutation.isPending}
                  disabled={!labelDraft.trim()}
                  aria-label="Salva nome"
                >
                  <Check className="size-4" aria-hidden="true" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsEditingLabel(false)}
                  aria-label="Annulla"
                >
                  <X className="size-4" aria-hidden="true" />
                </Button>
              </form>
            ) : (
              <div className="group flex items-center gap-2">
                <h1 className="truncate text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {pkg.label ?? pkg.tracking_number}
                </h1>
                <button
                  type="button"
                  onClick={() => {
                    setLabelDraft(pkg.label ?? "");
                    setIsEditingLabel(true);
                  }}
                  aria-label="Rinomina tracker"
                  className="text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                >
                  <Pencil className="size-4" aria-hidden="true" />
                </button>
              </div>
            )}
            <p className="font-mono text-sm text-slate-500 dark:text-slate-400">
              {pkg.tracking_number}
            </p>
          </div>
          <StatusPill status={pkg.status} />
        </div>

        <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-slate-500 dark:text-slate-400">Corriere</dt>
            <dd className="font-medium text-slate-900 dark:text-slate-100">{pkg.carrier.name}</dd>
          </div>
          <div>
            <dt className="text-slate-500 dark:text-slate-400">Metodo</dt>
            <dd className="font-medium text-slate-900 dark:text-slate-100">
              {pkg.provider.display_name}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500 dark:text-slate-400">Negozio</dt>
            <dd className="font-medium text-slate-900 dark:text-slate-100">
              {pkg.shop?.name ?? "-"}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500 dark:text-slate-400">Ultimo controllo</dt>
            <dd className="font-medium text-slate-900 dark:text-slate-100">
              {pkg.last_checked_at ? formatDateTime(pkg.last_checked_at) : "mai"}
            </dd>
          </div>
        </dl>

        {refreshError && <ErrorBanner message={refreshError} />}

        <div className="flex flex-wrap gap-2">
          <Button onClick={() => refreshMutation.mutate()} isLoading={refreshMutation.isPending}>
            <RefreshCw className="size-4" aria-hidden="true" />
            Aggiorna
          </Button>
          <Link to={`/packages/${pkg.id}/edit`}>
            <Button variant="secondary" type="button">
              <SlidersHorizontal className="size-4" aria-hidden="true" />
              Modifica dettagli
            </Button>
          </Link>
          <Button
            variant="secondary"
            onClick={() => archiveMutation.mutate()}
            isLoading={archiveMutation.isPending}
          >
            {pkg.is_archived ? (
              <ArchiveRestore className="size-4" aria-hidden="true" />
            ) : (
              <Archive className="size-4" aria-hidden="true" />
            )}
            {pkg.is_archived ? "Ripristina" : "Archivia"}
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              if (confirm("Eliminare definitivamente questo tracker?")) {
                deleteMutation.mutate();
              }
            }}
            isLoading={deleteMutation.isPending}
          >
            <Trash2 className="size-4" aria-hidden="true" />
            Elimina
          </Button>
        </div>
      </Card>

      <Card>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Cronologia
        </h2>
        <Timeline events={pkg.events} />
      </Card>
    </div>
  );
}
