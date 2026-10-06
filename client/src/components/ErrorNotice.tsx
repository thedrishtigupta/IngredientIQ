import { API_URL, ApiError } from "@/lib/api";

/** Shown when an API call fails. Says clearly when the API simply is not running. */
export function ErrorNotice({ error }: { error: unknown }) {
  const apiError = error instanceof ApiError ? error : null;
  const unreachable = apiError !== null && apiError.status === null;
  const message = error instanceof Error ? error.message : String(error);

  return (
    <div role="alert" className="border border-dashed border-border-strong px-6 py-12">
      <p className="eyebrow">
        {unreachable ? "API not reachable" : `API error${apiError?.status ? ` · ${apiError.status}` : ""}`}
      </p>
      <p className="display mt-2 text-2xl">
        {unreachable ? "The IngredientIQ API is not responding" : "The API could not answer this request"}
      </p>
      <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">{message}</p>
      {unreachable ? (
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">
          Start it from the project root with{" "}
          <code className="numeric text-foreground">
            .venv\Scripts\python.exe -m uvicorn src.api.main:app --port 8000
          </code>{" "}
          (and make sure the database container is running), then try again. This page calls{" "}
          <span className="numeric text-foreground">{API_URL}</span>; set VITE_API_URL to change it.
        </p>
      ) : null}
    </div>
  );
}
