import EditorWorker from "monaco-editor/editor/editor.worker?worker";
import JsonWorker from "monaco-editor/language/json/json.worker?worker";
import TsWorker from "monaco-editor/language/typescript/ts.worker?worker";

// Vite has no automatic Monaco worker wiring like webpack's monaco-editor-webpack-plugin,
// so we point MonacoEnvironment at the `?worker` bundles for the languages we actually use.
self.MonacoEnvironment = {
  getWorker(_workerId: string, label: string) {
    if (label === "json") return new JsonWorker();
    if (label === "typescript" || label === "javascript") return new TsWorker();
    return new EditorWorker();
  },
};
