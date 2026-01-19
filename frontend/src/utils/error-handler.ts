export type ErrorHandler<T> =
  | ({
      ok: true;
      error?: unknown;
      // success: boolean;
    } & Awaited<T>)
  | {
      ok: false;
      message: string;
      error?: unknown;
      // success: boolean;
    };

export async function errorHandler<T>(
  callback: () => Promise<T>
): Promise<ErrorHandler<T>> {
  try {
    const response = await callback();
    return { ok: true, ...response };
  } catch (error: unknown) {
    const message = (error as Error).message || "Something went wrong";
    return { message, ok: false, error };
  }
}
