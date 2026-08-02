import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

function collect(directory) {
  const files = [];
  for (const entry of readdirSync(directory)) {
    const full = join(directory, entry);
    if (entry === "node_modules" || entry === ".next") continue;
    if (statSync(full).isDirectory()) files.push(...collect(full));
    else if ((full.endsWith(".ts") || full.endsWith(".tsx")) && !full.endsWith(".d.ts")) files.push(full);
  }
  return files;
}

async function loadTypeScript() {
  try {
    return await import("typescript");
  } catch {
    const root = execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim();
    return import(pathToFileURL(join(root, "typescript/lib/typescript.js")).href);
  }
}

const ts = await loadTypeScript();
const files = collect(new URL("../web", import.meta.url).pathname);
let failed = false;
for (const file of files) {
  const source = readFileSync(file, "utf8");
  const result = ts.transpileModule(source, {
    fileName: file,
    reportDiagnostics: true,
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ESNext,
      jsx: ts.JsxEmit.ReactJSX,
      strict: true,
    },
  });
  for (const diagnostic of result.diagnostics ?? []) {
    if (diagnostic.category === ts.DiagnosticCategory.Error) {
      failed = true;
      const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, "\n");
      console.error(`${file}: ${message}`);
    }
  }
}
if (failed) process.exit(1);
console.log(`Frontend syntax OK: ${files.length} TypeScript files`);
