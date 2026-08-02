const RELATIVE_TIME_FORMATTER = new Intl.RelativeTimeFormat("it", { numeric: "auto" });
const DATE_TIME_FORMATTER = new Intl.DateTimeFormat("it", {
  dateStyle: "medium",
  timeStyle: "short",
});

const DIVISIONS: { amount: number; unit: Intl.RelativeTimeFormatUnit }[] = [
  { amount: 60, unit: "seconds" },
  { amount: 60, unit: "minutes" },
  { amount: 24, unit: "hours" },
  { amount: 7, unit: "days" },
  { amount: 4.35, unit: "weeks" },
  { amount: 12, unit: "months" },
  { amount: Number.POSITIVE_INFINITY, unit: "years" },
];

export function formatRelativeTime(isoDate: string): string {
  let duration = (new Date(isoDate).getTime() - Date.now()) / 1000;

  for (const division of DIVISIONS) {
    if (Math.abs(duration) < division.amount) {
      return RELATIVE_TIME_FORMATTER.format(Math.round(duration), division.unit);
    }
    duration /= division.amount;
  }
  return RELATIVE_TIME_FORMATTER.format(Math.round(duration), "years");
}

export function formatDateTime(isoDate: string): string {
  return DATE_TIME_FORMATTER.format(new Date(isoDate));
}
