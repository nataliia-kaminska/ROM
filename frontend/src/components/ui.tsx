import { type ReactNode, useMemo, useState } from "react";
import type { ProfileDetailsPayload } from "../api";
import type { Profile } from "../types";
import { label, splitList } from "../utils/format";

export function Field({
  labelText,
  value,
  onChange,
  type = "text",
  placeholder,
  disabled,
  list,
  title,
  required,
  className = "",
}: {
  labelText: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  list?: string;
  title?: string;
  required?: boolean;
  className?: string;
}) {
  return (
    <label className={`field ${className}`}>
      <span>{labelText}{required && <b className="required-mark">Required</b>}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        list={list}
        title={title}
        required={required}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

export function HelpTip({ text }: { text: string }) {
  return (
    <span className="help-tip" data-tip={text} aria-label={text} tabIndex={0}>
      ?
    </span>
  );
}

export function TextArea({
  labelText,
  value,
  onChange,
  placeholder,
  className = "span-2",
}: {
  labelText: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}) {
  return (
    <label className={`field ${className}`}>
      <span>{labelText}</span>
      <textarea value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} rows={4} />
    </label>
  );
}

export function MultiValueField({
  labelText,
  values,
  onChange,
  placeholder = "Comma-separated values",
  help,
  suggestions = [],
  suggestionsOnFocusOnly = false,
  className = "",
}: {
  labelText: string;
  values: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  help?: string;
  suggestions?: string[];
  suggestionsOnFocusOnly?: boolean;
  className?: string;
}) {
  const [draft, setDraft] = useState("");
  const normalizedValues = useMemo(() => new Set(values.map((value) => value.toLowerCase())), [values]);
  const visibleSuggestions = suggestions.filter((suggestion) => suggestion && !normalizedValues.has(suggestion.toLowerCase())).slice(0, 6);

  function addValue(nextValue = draft) {
    const nextValues = splitList(nextValue).length ? splitList(nextValue) : [nextValue.trim().replace(/,$/, "")];
    const uniqueValues = nextValues.filter((item) => item && !normalizedValues.has(item.toLowerCase()));
    if (uniqueValues.length === 0) {
      setDraft("");
      return;
    }
    onChange([...values, ...uniqueValues]);
    setDraft("");
  }

  function removeValue(value: string) {
    onChange(values.filter((item) => item !== value));
  }

  return (
    <div className={`field ${className}`}>
      <span>
        {labelText}
        {help && <HelpTip text={help} />}
      </span>
      <div className="tag-editor">
        {values.map((value) => (
          <button key={value} type="button" title="Remove" onClick={() => removeValue(value)}>
            {value}
          </button>
        ))}
        <input
          value={draft}
          placeholder={values.length ? "Add another..." : placeholder}
          onBlur={() => addValue()}
          onChange={(event) => {
            const value = event.target.value;
            if (value.endsWith(",")) {
              addValue(value);
            } else {
              setDraft(value);
            }
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === ",") {
              event.preventDefault();
              addValue();
            }
          }}
        />
      </div>
      {visibleSuggestions.length > 0 && (
        <div className={`suggestions${suggestionsOnFocusOnly ? " suggestions-focus-only" : ""}`}>
          {visibleSuggestions.map((suggestion) => (
            <button key={suggestion} type="button" onClick={() => addValue(suggestion)}>
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function JsonTextArea({
  labelText,
  value,
  onChange,
}: {
  labelText: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return <TextArea className="span-2 mono-field" labelText={labelText} value={value} onChange={onChange} />;
}

export function ActionButton({
  children,
  busy,
  variant = "primary",
  type = "submit",
  onClick,
  disabled,
  className = "",
}: {
  children: ReactNode;
  busy?: boolean;
  variant?: "primary" | "secondary";
  type?: "submit" | "button";
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button className={`${variant} ${className}`} type={type} onClick={onClick} disabled={busy || disabled}>
      {busy && <span className="spinner" aria-hidden="true" />}
      {busy ? "Working..." : children}
    </button>
  );
}

export function SkeletonCards({ count = 6 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }, (_, index) => (
        <article className="opportunity-card skeleton-card" key={index}>
          <span />
          <strong />
          <p />
          <p />
        </article>
      ))}
    </>
  );
}

export function ProfileCompleteness({ profile, details }: { profile: Profile | null; details: ProfileDetailsPayload }) {
  const checks = [
    Boolean(profile?.full_name),
    Boolean(profile?.email),
    Boolean(profile?.country),
    Boolean(profile?.disciplines.length),
    Boolean(profile?.keywords.length),
    Boolean(details.research_summary),
    Boolean(details.publications.length),
    Boolean(details.languages.length),
  ];
  const score = Math.round((checks.filter(Boolean).length / checks.length) * 100);
  return (
    <div className="completeness">
      <div>
        <span>Profile completeness</span>
        <strong>{score}%</strong>
      </div>
      <div className="progress"><i style={{ width: `${score}%` }} /></div>
    </div>
  );
}

export function SelectField<T extends string>({
  labelText,
  value,
  options,
  onChange,
  required,
  className = "",
}: {
  labelText: string;
  value: T;
  options: T[];
  onChange: (value: T) => void;
  required?: boolean;
  className?: string;
}) {
  return (
    <label className={`field ${className}`}>
      <span>{labelText}{required && <b className="required-mark">Required</b>}</span>
      <select value={value} required={required} onChange={(event) => onChange(event.target.value as T)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {label(option)}
          </option>
        ))}
      </select>
    </label>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty">
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

export function ToastStack({ notice, error }: { notice: string; error: string }) {
  if (!notice && !error) return null;
  return (
    <div className="toast-stack" aria-live="polite" aria-atomic="true">
      {error && (
        <div className="toast error">
          <strong>Action failed</strong>
          <span>{error}</span>
        </div>
      )}
      {notice && (
        <div className="toast success">
          <strong>Done</strong>
          <span>{notice}</span>
        </div>
      )}
    </div>
  );
}
