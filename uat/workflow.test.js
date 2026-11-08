import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

test("UAT runner uses the Ubuntu release supported by pinned Chromium", () => {
  const workflow = readFileSync(new URL("../.github/workflows/uat.yml", import.meta.url), "utf8");
  assert.match(workflow, /runs-on: ubuntu-24\.04\b/);
  assert.doesNotMatch(workflow, /runs-on: ubuntu-latest\b/);
});
