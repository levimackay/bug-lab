import { useRef } from "react";

export interface TabDef {
  id: string;
  label: string;
}

interface TabListProps {
  tabs: TabDef[];
  active: string;
  onChange: (id: string) => void;
  idPrefix: string;
}

export function TabList({ tabs, active, onChange, idPrefix }: TabListProps) {
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});

  function onKeyDown(e: React.KeyboardEvent) {
    const index = tabs.findIndex((t) => t.id === active);
    if (index === -1) return;
    let nextIndex: number | null = null;
    if (e.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
    else if (e.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
    else if (e.key === "Home") nextIndex = 0;
    else if (e.key === "End") nextIndex = tabs.length - 1;
    if (nextIndex !== null) {
      e.preventDefault();
      const next = tabs[nextIndex];
      onChange(next.id);
      refs.current[next.id]?.focus();
    }
  }

  return (
    <div role="tablist" className="flex border-b border-line" onKeyDown={onKeyDown}>
      {tabs.map((tab) => {
        const isActive = tab.id === active;
        return (
          <button
            key={tab.id}
            ref={(el) => {
              refs.current[tab.id] = el;
            }}
            role="tab"
            id={`${idPrefix}-tab-${tab.id}`}
            aria-selected={isActive}
            aria-controls={`${idPrefix}-panel-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onChange(tab.id)}
            className={
              "focus-ring border-r border-line px-2 py-1.5 font-mono text-2xs uppercase tracking-caps transition-colors " +
              (isActive ? "bg-raised text-ink" : "text-ink-faint hover:text-ink-dim")
            }
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({
  id,
  idPrefix,
  active,
  children,
}: {
  id: string;
  idPrefix: string;
  active: string;
  children: React.ReactNode;
}) {
  if (id !== active) return null;
  return (
    <div role="tabpanel" id={`${idPrefix}-panel-${id}`} aria-labelledby={`${idPrefix}-tab-${id}`} className="flex-1 overflow-auto">
      {children}
    </div>
  );
}
