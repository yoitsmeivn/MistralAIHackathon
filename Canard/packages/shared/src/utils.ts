declare function setTimeout(handler: () => void, timeout: number): unknown;

export function generateId(): string {
  const random = Math.random().toString(36).slice(2, 10);
  return `id_${Date.now()}_${random}`;
}

export function formatTimestamp(date = new Date()): string {
  return date.toISOString();
}

export async function delay(ms: number): Promise<void> {
  await new Promise<void>((resolve) => {
    setTimeout(resolve, ms);
  });
}
