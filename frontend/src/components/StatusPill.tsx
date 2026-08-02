import { AlertTriangle, CheckCircle2, HelpCircle, PackagePlus, Send, Truck } from "lucide-react";

import type { PackageStatus } from "@/api/types";

const STATUS_CONFIG: Record<
  PackageStatus,
  { label: string; icon: typeof Truck; className: string }
> = {
  created: {
    label: "Creato",
    icon: PackagePlus,
    className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  },
  in_transit: {
    label: "In transito",
    icon: Truck,
    className: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  },
  out_for_delivery: {
    label: "In consegna",
    icon: Send,
    className: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  },
  delivered: {
    label: "Consegnato",
    icon: CheckCircle2,
    className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  },
  exception: {
    label: "Anomalia",
    icon: AlertTriangle,
    className: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  },
  unknown: {
    label: "Sconosciuto",
    icon: HelpCircle,
    className: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
  },
};

export function StatusPill({ status }: { status: PackageStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${config.className}`}
    >
      <Icon className="size-3.5" aria-hidden="true" />
      {config.label}
    </span>
  );
}
