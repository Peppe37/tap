import { MapPin } from "lucide-react";

import type { TrackingEvent } from "@/api/types";
import { StatusPill } from "@/components/StatusPill";
import { formatDateTime } from "@/lib/format";

export function Timeline({ events }: { events: TrackingEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-slate-500 dark:text-slate-400">
        Nessun evento disponibile. Aggiorna il pacco per recuperare la cronologia.
      </p>
    );
  }

  return (
    <ol className="flex flex-col gap-0">
      {events.map((event, index) => (
        <li key={event.id} className="relative flex gap-4 pb-6 last:pb-0">
          {index < events.length - 1 && (
            <span
              className="absolute left-[7px] top-4 h-full w-px bg-slate-200 dark:bg-slate-700"
              aria-hidden="true"
            />
          )}
          <span className="relative mt-1.5 size-3.5 shrink-0 rounded-full border-2 border-brand-600 bg-white dark:bg-slate-900" />
          <div className="flex flex-1 flex-col gap-1">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                {event.description}
              </span>
              <StatusPill status={event.status} />
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
              <span>{formatDateTime(event.occurred_at)}</span>
              {event.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="size-3" aria-hidden="true" />
                  {event.location}
                </span>
              )}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
