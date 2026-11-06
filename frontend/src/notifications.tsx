import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";

type Kind = "success" | "error";
type Notify = (kind: Kind, text: string) => void;

const NotifyContext = createContext<Notify>(() => {});

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<{ id: number; kind: Kind; text: string }[]>([]);
  const nextId = useRef(0);

  const notify = useCallback<Notify>((kind, text) => {
    const id = nextId.current++;
    setToasts((current) => [...current, { id, kind, text }]);
    setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), 5000);
  }, []);

  return (
    <NotifyContext.Provider value={notify}>
      {children}
      <div className="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.kind}`} role={t.kind === "error" ? "alert" : "status"}>
            {t.text}
          </div>
        ))}
      </div>
    </NotifyContext.Provider>
  );
}

export const useNotify = () => useContext(NotifyContext);
