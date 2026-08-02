import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorBanner } from "@/components/Feedback";
import { Field, Input } from "@/components/Input";

export function FirstRunSetup() {
  const { completeSetup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (password.length < 10) {
      setError("La password deve contenere almeno 10 caratteri.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Le due password non coincidono.");
      return;
    }

    setIsSubmitting(true);
    try {
      await completeSetup(email, password);
      void navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossibile completare la configurazione.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <div className="flex size-12 items-center justify-center rounded-xl bg-brand-600 text-white">
            <ShieldCheck className="size-6" aria-hidden="true" />
          </div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Benvenuto su tap
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Questa istanza non ha ancora un account amministratore. Crealo per iniziare a tracciare
            i tuoi pacchi.
          </p>
        </div>
        <Card>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Field label="Email" htmlFor="email">
              <Input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>
            <Field label="Password" htmlFor="password" helpText="Almeno 10 caratteri.">
              <Input
                id="password"
                type="password"
                required
                minLength={10}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <Field label="Conferma password" htmlFor="confirm-password">
              <Input
                id="confirm-password"
                type="password"
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </Field>
            {error && <ErrorBanner message={error} />}
            <Button type="submit" isLoading={isSubmitting} className="mt-1 w-full">
              Crea account amministratore
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
