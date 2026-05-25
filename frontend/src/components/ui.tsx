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

export function PageHeader({
  title,
  description,
  hint,
  actions,
}: {
  title: string;
  description: string;
  hint?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <div className="title-with-help">
          <h1>{title}</h1>
          {hint && <HelpTip text={hint} />}
        </div>
        <p>{description}</p>
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </header>
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
  const [focused, setFocused] = useState(false);
  const normalizedValues = useMemo(() => new Set(values.map((value) => value.toLowerCase())), [values]);
  const draftQuery = draft.trim().toLowerCase();
  const visibleSuggestions = suggestions
    .filter((suggestion) => suggestion && !normalizedValues.has(suggestion.toLowerCase()))
    .filter((suggestion) => !draftQuery || suggestion.toLowerCase().includes(draftQuery))
    .slice(0, 6);
  const showSuggestions = visibleSuggestions.length > 0 && (!suggestionsOnFocusOnly || focused);

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
    <div
      className={`field ${className}`}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setFocused(false);
        }
      }}
      onFocus={() => setFocused(true)}
    >
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
      {showSuggestions && (
        <div className={`suggestions${suggestionsOnFocusOnly ? " suggestions-focus-only" : ""}`}>
          {visibleSuggestions.map((suggestion) => (
            <button key={suggestion} type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => addValue(suggestion)}>
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

export type SelectOption<T extends string> = {
  value: T;
  label: string;
  description?: string;
};

export function CustomSelect<T extends string>({
  value,
  options,
  onChange,
  placeholder = "Select...",
  ariaLabel,
  className = "",
}: {
  value: T;
  options: SelectOption<T>[];
  onChange: (value: T) => void;
  placeholder?: string;
  ariaLabel: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const selected = options.find((option) => option.value === value);
  return (
    <div className={`custom-select ${open ? "open" : ""} ${className}`}>
      <button
        className="custom-select-trigger"
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        onBlur={(event) => {
          if (!event.currentTarget.parentElement?.contains(event.relatedTarget as Node | null)) {
            setOpen(false);
          }
        }}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{selected?.label ?? placeholder}</span>
        <i aria-hidden="true">v</i>
      </button>
      {open && (
        <div className="custom-select-menu" role="listbox" tabIndex={-1}>
          {options.map((option) => (
            <button
              className={option.value === value ? "active" : ""}
              key={option.value}
              role="option"
              aria-selected={option.value === value}
              type="button"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => {
                onChange(option.value);
                setOpen(false);
              }}
            >
              <strong>{option.label}</strong>
              {option.description && <small>{option.description}</small>}
            </button>
          ))}
        </div>
      )}
    </div>
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
    { done: Boolean(profile?.full_name), label: "Add account name" },
    { done: Boolean(profile?.email), label: "Add account email" },
    { done: Boolean(profile?.country), label: "Add home country" },
    { done: Boolean(profile?.disciplines.length), label: "Add disciplines" },
    { done: Boolean(profile?.keywords.length), label: "Add keywords" },
    { done: Boolean(details.research_summary), label: "Add research summary" },
    { done: Boolean(details.publications.length), label: "Add publications" },
    { done: Boolean(details.languages.length), label: "Add languages" },
  ];
  const score = Math.round((checks.filter((check) => check.done).length / checks.length) * 100);
  if (score >= 100) return null;
  const missing = checks.filter((check) => !check.done).map((check) => check.label);
  const hint = missing.length ? `For 100%: ${missing.join(", ")}` : "Profile is complete.";
  return (
    <div className="completeness" title={hint} data-tip={hint}>
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
  const selectOptions = options.map((option) => ({ value: option, label: label(option) }));
  return (
    <div className={`field ${className}`}>
      <span>{labelText}{required && <b className="required-mark">Required</b>}</span>
      <CustomSelect value={value} options={selectOptions} onChange={onChange} ariaLabel={labelText} />
    </div>
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
