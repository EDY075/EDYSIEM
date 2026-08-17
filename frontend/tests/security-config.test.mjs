import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("Vite remains loopback-only by default", async () => {
  const config = await readFile(new URL("../vite.config.ts", import.meta.url), "utf8");
  assert.match(config, /host:\s*["']127\.0\.0\.1["']/);
  assert.match(config, /target:\s*["']http:\/\/127\.0\.0\.1:8080["']/);
  assert.doesNotMatch(config, /host:\s*true/);
  assert.doesNotMatch(config, /VITE_PROXY_TARGET|loadEnv/);
});

test("API keys use session storage and are attached by the central client", async () => {
  const client = await readFile(new URL("../src/api/client.ts", import.meta.url), "utf8");
  assert.match(client, /sessionStorage\.setItem/);
  assert.match(client, /"X-API-Key"/);
  assert.doesNotMatch(client, /localStorage\.setItem\(API_KEY_STORAGE/);
  assert.doesNotMatch(client, /VITE_API_KEY/);
});

test("the frontend never invents a comment author", async () => {
  const page = await readFile(new URL("../src/pages/CaseCenterPage.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(page, /author\s*:\s*["']analyst@edy["']/);
});

test("the vulnerable nanoid release is overridden", async () => {
  const manifest = JSON.parse(
    await readFile(new URL("../package.json", import.meta.url), "utf8"),
  );
  assert.equal(manifest.overrides.nanoid, "3.3.18");
});
