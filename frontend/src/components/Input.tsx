import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

interface FieldWrapperProps {
  label: string;
  htmlFor: string;
  error?: string | null;
  helpText?: string | null;
  children: ReactNode;
}

export function Field({ label, htmlFor, error, helpText, children }: FieldWrapperProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={htmlFor} className="text-sm font-medium text-slate-700 dark:text-slate-300">
        {label}
      </label>
      {children}
      {helpText && !error && (
        <p className="text-xs text-slate-500 dark:text-slate-400">{helpText}</p>
      )}
      {error && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}

const inputClasses =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 " +
  "placeholder:text-slate-400 focus:border-brand-500 focus:outline focus:outline-2 " +
  "focus:outline-brand-500/30 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={inputClasses} {...props} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={inputClasses} {...props} />;
}
