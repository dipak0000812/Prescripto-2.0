export function formatLocaleDate(
  dateInput: string | number | Date | null | undefined,
  locale: string = 'en',
  options?: Intl.DateTimeFormatOptions
): string {
  if (!dateInput) return '—';

  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return '—';

  const localeMap: Record<string, string> = {
    en: 'en-IN',
    hi: 'hi-IN',
    gu: 'gu-IN',
    mr: 'mr-IN',
  };

  const resolvedLocale = localeMap[locale] || 'en-IN';

  const now = new Date();
  const isToday =
    d.getDate() === now.getDate() &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear();

  const isYesterday =
    d.getDate() === now.getDate() - 1 &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear();

  const timeString = d.toLocaleTimeString(resolvedLocale, {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });

  if (isToday) {
    if (locale === 'hi') return `आज, ${timeString}`;
    if (locale === 'gu') return `આજે, ${timeString}`;
    if (locale === 'mr') return `आज, ${timeString}`;
    return `Today, ${timeString}`;
  }

  if (isYesterday) {
    if (locale === 'hi') return `कल, ${timeString}`;
    if (locale === 'gu') return `ગઈકાલે, ${timeString}`;
    if (locale === 'mr') return `काल, ${timeString}`;
    return `Yesterday, ${timeString}`;
  }

  const defaultOptions: Intl.DateTimeFormatOptions = {
    day: 'numeric',
    month: 'short',
    year: d.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    ...options,
  };

  return d.toLocaleDateString(resolvedLocale, defaultOptions);
}

export function getTimeBasedGreeting(name: string, locale: string = 'en'): string {
  const hour = new Date().getHours();
  const cleanName = name ? name.split(' ')[0] : '';

  if (hour < 12) {
    if (locale === 'hi') return `सुप्रभात${cleanName ? `, ${cleanName}` : ''}`;
    if (locale === 'gu') return `શુભ સવાર${cleanName ? `, ${cleanName}` : ''}`;
    if (locale === 'mr') return `शुभ प्रभात${cleanName ? `, ${cleanName}` : ''}`;
    return `Good morning${cleanName ? `, ${cleanName}` : ''}`;
  }

  if (hour < 17) {
    if (locale === 'hi') return `नमस्ते${cleanName ? `, ${cleanName}` : ''}`;
    if (locale === 'gu') return `નમસ્તે${cleanName ? `, ${cleanName}` : ''}`;
    if (locale === 'mr') return `नमस्कार${cleanName ? `, ${cleanName}` : ''}`;
    return `Good afternoon${cleanName ? `, ${cleanName}` : ''}`;
  }

  if (locale === 'hi') return `शुभ संध्या${cleanName ? `, ${cleanName}` : ''}`;
  if (locale === 'gu') return `શુભ સાંજ${cleanName ? `, ${cleanName}` : ''}`;
  if (locale === 'mr') return `शुभ संध्याकाळ${cleanName ? `, ${cleanName}` : ''}`;
  return `Good evening${cleanName ? `, ${cleanName}` : ''}`;
}

