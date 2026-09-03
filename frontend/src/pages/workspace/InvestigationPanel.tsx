import { TabList, TabPanel, type TabDef } from "../../components/TabList";
import { useWorkspaceContext } from "./WorkspaceContext";
import type { InvestigationTabId } from "./types";
import { IncidentTab } from "./tabs/IncidentTab";
import { LogsTab } from "./tabs/LogsTab";
import { TraceTab } from "./tabs/TraceTab";
import { TestsTab } from "./tabs/TestsTab";
import { RuntimeTab } from "./tabs/RuntimeTab";
import { HypothesisTab } from "./tabs/HypothesisTab";
import { HintsTab } from "./tabs/HintsTab";

const ALWAYS_TABS: TabDef[] = [
  { id: "incident", label: "Incident" },
  { id: "tests", label: "Tests" },
  { id: "hypothesis", label: "Hypothesis" },
  { id: "hints", label: "Hints" },
];

const TOOL_TABS: Record<string, TabDef> = {
  logs: { id: "logs", label: "Logs" },
  stack_trace: { id: "trace", label: "Trace" },
  runtime: { id: "runtime", label: "Runtime" },
};

export function InvestigationPanel() {
  const { run, investigationTab, setInvestigationTab } = useWorkspaceContext();
  if (!run) return <div className="h-full border-l border-line" />;

  const toolTabs = run.incident.tools.map((t) => TOOL_TABS[t]).filter((t): t is TabDef => Boolean(t));
  const tabs: TabDef[] = [ALWAYS_TABS[0], ...toolTabs, ...ALWAYS_TABS.slice(1)];

  return (
    <div className="flex h-full flex-col overflow-hidden border-l border-line">
      <TabList tabs={tabs} active={investigationTab} onChange={(id) => setInvestigationTab(id as InvestigationTabId)} idPrefix="investigation" />
      <TabPanel id="incident" idPrefix="investigation" active={investigationTab}>
        <IncidentTab />
      </TabPanel>
      <TabPanel id="logs" idPrefix="investigation" active={investigationTab}>
        <LogsTab />
      </TabPanel>
      <TabPanel id="trace" idPrefix="investigation" active={investigationTab}>
        <TraceTab />
      </TabPanel>
      <TabPanel id="tests" idPrefix="investigation" active={investigationTab}>
        <TestsTab />
      </TabPanel>
      <TabPanel id="runtime" idPrefix="investigation" active={investigationTab}>
        <RuntimeTab />
      </TabPanel>
      <TabPanel id="hypothesis" idPrefix="investigation" active={investigationTab}>
        <HypothesisTab />
      </TabPanel>
      <TabPanel id="hints" idPrefix="investigation" active={investigationTab}>
        <HintsTab />
      </TabPanel>
    </div>
  );
}
