import assert from "node:assert/strict";
import { existsSync, statSync } from "node:fs";
import { afterEach, before, test } from "node:test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { build } from "esbuild";
import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { fileURLToPath, pathToFileURL } from "node:url";

class MemoryStorage {
  #values = new Map();

  clear() {
    this.#values.clear();
  }

  getItem(key) {
    return this.#values.get(key) ?? null;
  }

  removeItem(key) {
    this.#values.delete(key);
  }

  setItem(key, value) {
    this.#values.set(key, String(value));
  }
}

const session = new MemoryStorage();
let localStorageAccesses = 0;
const forbiddenLocalStorage = {
  getItem() {
    localStorageAccesses += 1;
    throw new Error("authentication must not read localStorage");
  },
  removeItem() {
    localStorageAccesses += 1;
    throw new Error("authentication must not mutate localStorage");
  },
  setItem() {
    localStorageAccesses += 1;
    throw new Error("authentication must not mutate localStorage");
  },
};

Object.defineProperty(globalThis, "sessionStorage", {
  configurable: true,
  value: session,
});
Object.defineProperty(globalThis, "localStorage", {
  configurable: true,
  value: forbiddenLocalStorage,
});
Object.defineProperty(globalThis, "navigator", {
  configurable: true,
  value: { language: "en-US" },
});

let AuthGate;
let useAuth;
let apiClient;
let hasOperatorApiKey;
let setOperatorApiKey;
let getAuthIdentityPresentation;
let originalAuthenticate;

before(async () => {
  const frontendRoot = fileURLToPath(new URL("..", import.meta.url));
  const runtimeDirectory = fileURLToPath(
    new URL("../node_modules/.cache/edysiem-auth-tests/", import.meta.url),
  );
  const runtimeModule = fileURLToPath(
    new URL("../node_modules/.cache/edysiem-auth-tests/auth-bundle.mjs", import.meta.url),
  );
  await mkdir(runtimeDirectory, { recursive: true });
  const localSourceResolver = {
    name: "edysiem-local-source-resolver",
    setup(builder) {
      builder.onResolve({ filter: /^\./ }, (args) => {
        const base = path.resolve(args.resolveDir, args.path);
        const candidates = [
          base,
          `${base}.ts`,
          `${base}.tsx`,
          `${base}.js`,
          `${base}.jsx`,
          path.join(base, "index.ts"),
          path.join(base, "index.tsx"),
        ];
        const resolved = candidates.find(
          (candidate) => existsSync(candidate) && statSync(candidate).isFile(),
        );
        return resolved ? { path: resolved } : null;
      });
    },
  };
  await build({
    absWorkingDir: frontendRoot,
    bundle: true,
    define: { "import.meta.env": "{}" },
    external: ["react", "react/*"],
    format: "esm",
    jsx: "automatic",
    outfile: runtimeModule,
    packages: "external",
    platform: "node",
    plugins: [localSourceResolver],
    stdin: {
      contents: [
        'export { AuthGate } from "./src/auth/AuthGate.tsx";',
        'export { useAuth, getAuthIdentityPresentation } from "./src/auth/AuthContext.tsx";',
        'export { apiClient, hasOperatorApiKey, setOperatorApiKey } from "./src/api/client.ts";',
      ].join("\n"),
      resolveDir: frontendRoot,
      sourcefile: "auth-test-entry.ts",
    },
  });
  ({
    AuthGate,
    apiClient,
    getAuthIdentityPresentation,
    hasOperatorApiKey,
    setOperatorApiKey,
    useAuth,
  } = await import(`${pathToFileURL(runtimeModule).href}?run=${Date.now()}`));
  originalAuthenticate = apiClient.authenticate;
});

afterEach(() => {
  apiClient.authenticate = originalAuthenticate;
  setOperatorApiKey("");
  session.clear();
  localStorageAccesses = 0;
});

async function renderGate(language, child = React.createElement("div", null, "protected")) {
  let renderer;
  await act(async () => {
    renderer = TestRenderer.create(React.createElement(AuthGate, { language }, child));
  });
  return renderer;
}

async function enterKey(renderer, key) {
  await act(async () => {
    renderer.root.findByType("input").props.onChange({ target: { value: key } });
  });
  await act(async () => {
    await renderer.root.findByType("form").props.onSubmit({ preventDefault() {} });
  });
}

test("missing key stays behind the AuthGate in pt-BR and English", async () => {
  let calls = 0;
  apiClient.authenticate = async () => {
    calls += 1;
    return { success: false, error: { code: "401", message: "invalid", status: 401 } };
  };

  const ptGate = await renderGate("pt-BR");
  assert.equal(ptGate.root.findByType("h1").children.join(""), "Autenticação necessária");
  assert.equal(calls, 0);
  ptGate.unmount();

  const enGate = await renderGate("en-US");
  assert.equal(enGate.root.findByType("h1").children.join(""), "Authentication required");
  assert.equal(calls, 0);
  enGate.unmount();
});

test("invalid key is removed from sessionStorage and never unlocks children", async () => {
  const invalidKey = "invalid-operator-key-with-at-least-32-bytes";
  apiClient.authenticate = async () => ({
    success: false,
    error: { code: "401", message: "invalid", status: 401 },
  });
  const gate = await renderGate("en-US");

  await enterKey(gate, invalidKey);

  assert.equal(session.getItem("edysiem-api-key"), null);
  assert.equal(hasOperatorApiKey(), false);
  assert.match(gate.root.findByProps({ role: "alert" }).children.join(""), /Invalid credential/);
  assert.equal(localStorageAccesses, 0);
  assert.equal(gate.root.findAllByType("form").length, 1);
  gate.unmount();
});

test("valid key unlocks the real server identity and sign-out clears the session", async () => {
  const validKey = "valid-operator-key-with-at-least-32-random-bytes";
  apiClient.authenticate = async () => ({
    success: true,
    data: { identity: "soc.operator", role: "viewer", auth_type: "api_key" },
  });

  function SessionProbe() {
    const { identity, signOut } = useAuth();
    return React.createElement(
      "button",
      { type: "button", onClick: signOut },
      `${identity.identity}:${identity.role}`,
    );
  }

  const gate = await renderGate("en-US", React.createElement(SessionProbe));
  await enterKey(gate, validKey);

  const sessionButton = gate.root.findByType("button");
  assert.equal(sessionButton.children.join(""), "soc.operator:viewer");
  assert.equal(session.getItem("edysiem-api-key"), validKey);
  assert.equal(localStorageAccesses, 0);

  await act(async () => sessionButton.props.onClick());
  assert.equal(session.getItem("edysiem-api-key"), null);
  assert.equal(hasOperatorApiKey(), false);
  assert.equal(gate.root.findAllByType("form").length, 1);
  gate.unmount();
});

test("a valid key in sessionStorage is revalidated on mount", async () => {
  const storedKey = "stored-operator-key-with-at-least-32-random-bytes";
  setOperatorApiKey(storedKey);
  let calls = 0;
  apiClient.authenticate = async () => {
    calls += 1;
    return {
      success: true,
      data: { identity: "admin.local", role: "admin", auth_type: "api_key" },
    };
  };

  const gate = await renderGate("pt-BR");

  assert.equal(calls, 1);
  assert.equal(gate.root.findByType("div").children.join(""), "protected");
  assert.equal(session.getItem("edysiem-api-key"), storedKey);
  assert.equal(localStorageAccesses, 0);
  gate.unmount();
});

test("the user menu presents the literal server identity for every supported role", () => {
  const identities = [
    { identity: "viewer.local", role: "viewer", auth_type: "api_key" },
    { identity: "soc-analyst", role: "analyst", auth_type: "api_key" },
    { identity: "root.operator", role: "admin", auth_type: "api_key" },
  ];

  for (const identity of identities) {
    const presentation = getAuthIdentityPresentation(identity);
    assert.equal(presentation.identityLabel, identity.identity);
    assert.equal(presentation.roleLabel, identity.role);
    assert.equal(presentation.avatarLabel, identity.identity[0].toUpperCase());
    assert.equal(Object.values(presentation).some((value) => value.includes("@edy")), false);
  }
});
