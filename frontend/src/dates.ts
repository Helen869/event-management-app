// The API speaks UTC ISO strings; <input type="datetime-local"> speaks local "YYYY-MM-DDTHH:mm".

const pad = (n: number) => String(n).padStart(2, "0");

export function toLocalInput(date: Date): string {
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

// A date-time string without an offset is parsed as local time, which is what the input holds.
export function localInputToUtc(value: string): string {
  return new Date(value).toISOString();
}

// Explicit fields: dateStyle/timeStyle cannot be combined with timeZoneName (throws a TypeError).
const formatter = new Intl.DateTimeFormat(undefined, {
  year: "numeric",
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZoneName: "short",
});

export function formatDateTime(iso: string): string {
  return formatter.format(new Date(iso));
}
