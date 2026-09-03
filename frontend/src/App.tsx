import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ToastProvider } from "./components/ToastProvider";
import Dashboard from "./pages/Dashboard";
import IncidentBrowser from "./pages/IncidentBrowser";
import IncidentReport from "./pages/IncidentReport";
import Workspace from "./pages/workspace/Workspace";
import Resolved from "./pages/Resolved";

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incidents" element={<IncidentBrowser />} />
          <Route path="/incidents/:id" element={<IncidentReport />} />
          <Route path="/runs/:id" element={<Workspace />} />
          <Route path="/runs/:id/resolved" element={<Resolved />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}
