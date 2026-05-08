export function formatDateTimeToChina(value) {
  if (value === undefined || value === null || value === "" || value === "-") return "-";

  const raw = String(value).trim();
  if (!raw) return "-";

  const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(raw);

  // No explicit timezone: treat backend time as UTC, then convert to Asia/Shanghai.
  if (!hasTimezone) {
    const match = raw.match(
      /^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?$/
    );
    if (match) {
      const [, y, m, d, hh, mm, ss] = match;
      const utcDate = new Date(
        Date.UTC(
          Number(y),
          Number(m) - 1,
          Number(d),
          Number(hh),
          Number(mm),
          Number(ss)
        )
      );
      return formatDateByShanghai(utcDate);
    }
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;

  return formatDateByShanghai(date);
}

function formatDateByShanghai(date) {
  const formatter = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
  const parts = formatter.formatToParts(date);
  const pick = (type) => parts.find((p) => p.type === type)?.value || "";

  return `${pick("year")}-${pick("month")}-${pick("day")} ${pick("hour")}:${pick("minute")}:${pick("second")}`;
}
