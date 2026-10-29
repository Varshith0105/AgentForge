export function getErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: unknown } } }).response;
    const detail = response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (typeof item === 'object' && item !== null && 'msg' in item) {
            const message = (item as { msg?: unknown }).msg;
            return typeof message === 'string' ? message : null;
          }
          return null;
        })
        .filter((message): message is string => message !== null);
      if (messages.length > 0) return messages.join(', ');
    }
  }

  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
