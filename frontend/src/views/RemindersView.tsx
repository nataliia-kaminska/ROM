import { useState, type FormEvent } from "react";
import type { Opportunity, Reminder } from "../types";
import { formatDate, label } from "../utils/format";
import { CustomSelect, EmptyState, Field, HelpTip, PageHeader } from "../components/ui";

export function RemindersView({
  reminderForm,
  reminders,
  reminderEligibleOpportunities,
  opportunitiesById,
  onReminderFormChange,
  onCreateReminder,
  onCompleteReminder,
}: {
  reminderForm: { opportunity_id: string; remind_on: string; message: string };
  reminders: Reminder[];
  reminderEligibleOpportunities: Opportunity[];
  opportunitiesById: ReadonlyMap<number, Opportunity>;
  onReminderFormChange: (form: { opportunity_id: string; remind_on: string; message: string }) => void;
  onCreateReminder: (event: FormEvent) => void;
  onCompleteReminder: (reminderId: number) => void;
}) {
  const [composerOpen, setComposerOpen] = useState(false);
  const sortedReminders = [...reminders].sort((a, b) => a.remind_on.localeCompare(b.remind_on));
  return (
    <section className="reminders-page">
      <PageHeader
        title="Application reminders"
        description="A chronological timeline of upcoming application nudges tied to saved or planned opportunities."
        hint="Create reminders only for opportunities you saved or planned, so the list stays tied to real intent."
        actions={<button className="primary floating-add" type="button" onClick={() => setComposerOpen(true)}>+ Add reminder</button>}
      />
      <div className="panel reminder-timeline-panel">
      <div className="reminder-timeline">
        {sortedReminders.map((reminder) => {
          const opportunity = opportunitiesById.get(reminder.opportunity_id);
          return (
            <article className={`reminder-node ${urgencyClass(reminder.remind_on)} ${reminder.status === "completed" ? "completed" : ""}`} key={reminder.id}>
              <ReminderStatusIcon status={reminder.status} />
              <div>
                <div className="reminder-meta">
                  <span>{formatDate(reminder.remind_on)}</span>
                </div>
                <strong>{opportunity?.title ?? `Opportunity ${reminder.opportunity_id}`}</strong>
                <p>{reminder.message || "Application reminder"}</p>
              </div>
              {reminder.status === "pending" && (
                <button className="secondary" title="Mark this reminder as done so it leaves the pending workflow." onClick={() => onCompleteReminder(reminder.id)}>
                  Done
                </button>
              )}
            </article>
          );
        })}
        {reminders.length === 0 && <EmptyState title="No application reminders" detail="Saved, planned, and applied opportunities can generate deadline reminders automatically." />}
      </div>
      </div>
      {composerOpen && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" onClick={() => setComposerOpen(false)}>
          <form
            className="modal-card grid-form"
            onSubmit={(event) => {
              onCreateReminder(event);
              setComposerOpen(false);
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <div className="span-2 title-with-help">
              <h2>New reminder</h2>
              <HelpTip text="Pick a saved or planned opportunity, then choose the date when you want the app to nudge you." />
            </div>
            <div className="field span-2">
              <span>Opportunity</span>
              <CustomSelect
                value={reminderForm.opportunity_id}
                ariaLabel="Reminder opportunity"
                placeholder="Select a saved or planned opportunity"
                options={[
                  { value: "", label: "Select a saved or planned opportunity" },
                  ...reminderEligibleOpportunities.map((opportunity) => ({ value: String(opportunity.id), label: opportunity.title })),
                ]}
                onChange={(opportunity_id) => onReminderFormChange({ ...reminderForm, opportunity_id })}
              />
            </div>
            <Field labelText="Remind on" type="date" value={reminderForm.remind_on} onChange={(remind_on) => onReminderFormChange({ ...reminderForm, remind_on })} />
            <Field labelText="Message" value={reminderForm.message} onChange={(message) => onReminderFormChange({ ...reminderForm, message })} />
            <div className="actions span-2">
              <button className="primary">Create reminder</button>
              <button className="secondary" type="button" onClick={() => setComposerOpen(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}

function urgencyClass(value: string): string {
  const target = new Date(`${value}T00:00:00`);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.ceil((target.getTime() - today.getTime()) / 86400000);
  if (days <= 7) return "urgent";
  if (days <= 30) return "soon";
  return "later";
}

function ReminderStatusIcon({ status }: { status: Reminder["status"] }) {
  return (
    <div className={`reminder-icon reminder-icon-${status}`} title={label(status)} aria-label={label(status)}>
      {status === "completed" ? "✓" : "!"}
    </div>
  );
}
