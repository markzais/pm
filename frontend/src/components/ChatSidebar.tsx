import type { FormEvent } from "react";

type ChatMessage = {
  sender: "user" | "assistant";
  text: string;
};

type ChatSidebarProps = {
  messages: ChatMessage[];
  value: string;
  onChange: (value: string) => void;
  onSend: (message: string) => void;
  disabled: boolean;
  status?: string | null;
};

export const ChatSidebar = ({
  messages,
  value,
  onChange,
  onSend,
  disabled,
  status,
}: ChatSidebarProps) => {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!value.trim()) {
      return;
    }
    onSend(value.trim());
  };

  return (
    <aside className="flex min-h-[720px] flex-col rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-6 shadow-[var(--shadow)]">
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
          AI Assistant
        </p>
        <h2 className="mt-3 text-2xl font-semibold text-[var(--navy-dark)]">
          Chat with AI
        </h2>
        <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
          Ask the AI to add, move, or update cards on your Kanban board.
        </p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-3xl border border-[var(--stroke)] bg-white/80 p-4">
        {messages.length === 0 ? (
          <div className="text-sm text-[var(--gray-text)]">
            Start the chat to let AI update your board.
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${message.sender}-${index}`}
              className={`rounded-3xl px-4 py-3 text-sm shadow-sm ${
                message.sender === "user"
                  ? "bg-[var(--surface)] text-[var(--navy-dark)] self-end"
                  : "bg-[var(--primary-blue)] text-white"
              }`}
            >
              {message.text}
            </div>
          ))
        )}
      </div>

      <form className="mt-6 flex flex-col gap-3" onSubmit={handleSubmit}>
        <label className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
          New message
        </label>
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          rows={4}
          className="w-full rounded-3xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none"
          placeholder="Ask the AI to update the board..."
          disabled={disabled}
        />
        <div className="flex items-center justify-between gap-3">
          <button
            type="submit"
            disabled={disabled || !value.trim()}
            className="rounded-full bg-[var(--primary-purple)] px-5 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-60"
          >
            Send
          </button>
          <span className="text-xs text-[var(--gray-text)]">
            {status ?? "Ready"}
          </span>
        </div>
      </form>
    </aside>
  );
};
