import { useParams } from "react-router-dom";
import { WorkspaceProvider } from "./WorkspaceContext";
import { WorkspaceLayout } from "./WorkspaceLayout";

export default function Workspace() {
  const { id } = useParams<{ id: string }>();
  if (!id) return null;
  return (
    <WorkspaceProvider runId={id} key={id}>
      <WorkspaceLayout />
    </WorkspaceProvider>
  );
}
