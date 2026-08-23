import type { UserInfo } from "../types";

function initials(name: string) {
  return name.trim().charAt(0).toUpperCase();
}

export function LoginScreen({
  users,
  selectedUserId,
  onSelect,
  isLoading,
  error,
  onRetry,
}: {
  users: UserInfo[];
  selectedUserId: string;
  onSelect: (userId: string) => void;
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  const selectedUser = users.find((user) => user.user_id === selectedUserId);

  return (
    <section className="border-t border-slate-200 pt-7">
      <p className="font-mono text-xs font-medium uppercase tracking-[0.22em] text-blue-600">
        Staff access
      </p>
      <label className="mt-4 block text-sm text-ink" htmlFor="user-select">
        Signed in as
      </label>
      <div className="relative mt-2">
        <select
          id="user-select"
          value={selectedUserId}
          onChange={(event) => onSelect(event.target.value)}
          disabled={isLoading || Boolean(error)}
          className="min-h-16 w-full appearance-none rounded-2xl border border-slate-200 bg-white py-3 pl-16 pr-11 text-sm font-medium text-ink shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-ink"
        >
          <option value="">{isLoading ? "Loading users..." : "Select a user"}</option>
          {users.map((user) => (
            <option key={user.user_id} value={user.user_id}>
              {user.name} · {user.role}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute left-4 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-blue-50 text-sm font-semibold text-blue-600">
          {selectedUser ? initials(selectedUser.name) : "?"}
        </div>
        <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-ink" aria-hidden="true">
          ⌄
        </span>
      </div>
      {selectedUser ? (
        <p className="mt-2 pl-16 text-xs text-ink">{selectedUser.role}</p>
      ) : null}
      {error ? (
        <div className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 p-3">
          <p className="text-sm text-rose-800">{error}</p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 min-h-10 rounded-xl border border-rose-200 bg-white px-4 py-2 text-sm font-medium text-rose-800 transition hover:bg-rose-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 focus-visible:ring-offset-2"
          >
            Retry
          </button>
        </div>
      ) : (
        <div className="mt-6 flex gap-3 text-sm leading-7 text-ink">
          <span className="mt-1 text-base text-ink" aria-hidden="true">▣</span>
          <p>Backend permissions still apply. Viewer accounts can investigate but cannot execute actions.</p>
        </div>
      )}
    </section>
  );
}
