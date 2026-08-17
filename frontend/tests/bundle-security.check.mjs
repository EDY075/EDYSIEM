import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

async function bundledText(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const contents = [];
  for (const entry of entries) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) contents.push(await bundledText(target));
    else if (/\.(?:html|js|css|map)$/u.test(entry.name)) contents.push(await readFile(target, "utf8"));
  }
  return contents.flat().join("\n");
}

test("production bundle never contains an operator API key", async () => {
  const bundle = await bundledText(fileURLToPath(new URL("../dist", import.meta.url)));
  const sentinel = process.env.VITE_API_KEY_SENTINEL;
  assert.ok(sentinel, "VITE_API_KEY_SENTINEL must be set by the build/test command");
  assert.doesNotMatch(bundle, new RegExp(sentinel.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&"), "u"));
  assert.doesNotMatch(bundle, /replace-with-a-random-secret-of-at-least-32-bytes/u);
});
