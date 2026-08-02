import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ExternalLink, Unplug } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";

import { ApiError } from "@/api/client";
import {
  deleteCredential,
  getCredentialStatus,
  saveCredential,
  testCredential,
} from "@/api/providers";
import type { Provider } from "@/api/types";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorBanner } from "@/components/Feedback";
import { Field, Input } from "@/components/Input";

export function ConnectionGuideCard({ provider }: { provider: Provider }) {
  const queryClient = useQueryClient();
  const guide = provider.setup_guide;
  const [values, setValues] = useState<Record<string, string>>({});
  const [testResult, setTestResult] = useState<"idle" | "valid" | "invalid">("idle");
  const [error, setError] = useState<string | null>(null);

  const statusQuery = useQuery({
    queryKey: ["credential-status", provider.code],
    queryFn: () => getCredentialStatus(provider.code),
  });

  const testMutation = useMutation({
    mutationFn: () => testCredential(provider.code, values),
    onSuccess: (result) => {
      setTestResult(result.is_valid ? "valid" : "invalid");
      setError(null);
    },
    onError: (err: unknown) => {
      setError(err instanceof ApiError ? err.message : "Test di connessione non riuscito.");
      setTestResult("idle");
    },
  });

  const saveMutation = useMutation({
    mutationFn: () => saveCredential(provider.code, values),
    onSuccess: () => {
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["credential-status", provider.code] });
    },
    onError: (err: unknown) => {
      setError(err instanceof ApiError ? err.message : "Impossibile salvare la connessione.");
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: () => deleteCredential(provider.code),
    onSuccess: () => {
      setValues({});
      setTestResult("idle");
      void queryClient.invalidateQueries({ queryKey: ["credential-status", provider.code] });
    },
  });

  const handleTest = (event: FormEvent) => {
    event.preventDefault();
    testMutation.mutate();
  };

  const isConfigured = statusQuery.data?.is_configured ?? false;

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-slate-100">
            {provider.display_name}
          </h3>
          {guide?.intro && (
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{guide.intro}</p>
          )}
        </div>
        {isConfigured && (
          <span className="flex items-center gap-1 whitespace-nowrap rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
            <CheckCircle2 className="size-3.5" aria-hidden="true" />
            Connesso
          </span>
        )}
      </div>

      {guide?.steps && guide.steps.length > 0 && (
        <ol className="flex flex-col gap-2 text-sm text-slate-600 dark:text-slate-300">
          {guide.steps.map((step, index) => (
            <li key={step.title} className="flex gap-2">
              <span className="font-medium text-brand-600 dark:text-brand-400">{index + 1}.</span>
              <span>
                <span className="font-medium">{step.title}</span> &mdash; {step.description}
                {step.link && (
                  <a
                    href={step.link}
                    target="_blank"
                    rel="noreferrer"
                    className="ml-1 inline-flex items-center gap-0.5 text-brand-600 hover:underline dark:text-brand-400"
                  >
                    Apri <ExternalLink className="size-3" aria-hidden="true" />
                  </a>
                )}
              </span>
            </li>
          ))}
        </ol>
      )}

      <form onSubmit={handleTest} className="flex flex-col gap-3">
        {guide?.fields.map((field) => (
          <Field
            key={field.key}
            label={field.label}
            htmlFor={`${provider.code}-${field.key}`}
            helpText={field.help_text}
          >
            <Input
              id={`${provider.code}-${field.key}`}
              type={field.type === "password" ? "password" : "text"}
              required={field.required}
              value={values[field.key] ?? ""}
              onChange={(e) => {
                setValues((prev) => ({ ...prev, [field.key]: e.target.value }));
                setTestResult("idle");
              }}
            />
          </Field>
        ))}

        {error && <ErrorBanner message={error} />}
        {testResult === "valid" && (
          <p className="text-sm text-emerald-600 dark:text-emerald-400">
            Connessione verificata con successo.
          </p>
        )}
        {testResult === "invalid" && (
          <p className="text-sm text-red-600 dark:text-red-400">
            Le credenziali fornite non sono valide.
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <Button type="submit" variant="secondary" isLoading={testMutation.isPending}>
            Testa connessione
          </Button>
          <Button
            type="button"
            onClick={() => saveMutation.mutate()}
            isLoading={saveMutation.isPending}
          >
            Salva
          </Button>
          {isConfigured && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => disconnectMutation.mutate()}
              isLoading={disconnectMutation.isPending}
            >
              <Unplug className="size-4" aria-hidden="true" />
              Disconnetti
            </Button>
          )}
        </div>
      </form>
    </Card>
  );
}
