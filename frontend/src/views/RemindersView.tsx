import type { FormEvent } from "react";
import type { Opportunity, Reminder } from "../types";
import { label } from "../utils/format";
import { EmptyState, Field, HelpTip } from "../components/ui";

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
  return (
    <section className="panel">
      <div className="title-with-help">
        <h2>Reminders</h2>
        <HelpTip text="Create reminders only for opportunities you saved or planned, so the reminder list stays tied to real intent." />
      </div>
      <form className="grid-form" onSubmit={onCreateReminder}>
        <label className="field">
          <span>Opportunity</span>
          <select value={reminderForm.opportunity_id} onChange={(event) => onReminderFormChange({ ...reminderForm, opportunity_id: event.target.value })}>
            <option value="">Select a saved or planned opportunity</option>
            {reminderEligibleOpportunities.map((opportunity) => (
              <option value={opportunity.id} key={opportunity.id}>
                {opportunity.title}
              </option>
            ))}
          </select>
        </label>
        <Field labelText="Remind on" type="date" value={reminderForm.remind_on} onChange={(remind_on) => onReminderFormChange({ ...reminderForm, remind_on })} />
        <Field labelText="Message" value={reminderForm.message} onChange={(message) => onReminderFormChange({ ...reminderForm, message })} />
        <button className="primary">Create reminder</button>
      </form>
      <div className="table">
        {reminders.map((reminder) => (
          <div className="table-row" key={reminder.id}>
            <span>{opportunitiesById.get(reminder.opportunity_id)?.title ?? `Opportunity ${reminder.opportunity_id}`}</span>
            <span>{reminder.remind_on}</span>
            <span>{label(reminder.status)}</span>
            {reminder.status === "pending" && (
              <button className="secondary" title="Mark this reminder as done so it leaves the pending workflow." onClick={() => onCompleteReminder(reminder.id)}>
                Mark done
              </button>
            )}
          </div>
        ))}
        {reminders.length === 0 && <EmptyState title="No reminders" detail="Saved, planned, and applied opportunities can generate deadline reminders automatically." />}
      </div>
    </section>
  );
}
