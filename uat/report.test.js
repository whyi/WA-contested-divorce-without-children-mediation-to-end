import assert from "node:assert/strict";
import { test } from "node:test";
import { createReport, scenarioResult } from "./report.js";

test("report omits raw errors and always blocks authenticated sign-off", () => {
  const result = scenarioResult(
    { title: "SMOKE-01", unexpected: "secret" },
    { status: "failed", error: { message: "secret cookie" } },
  );
  const report = createReport("failed", [result]);
  assert.deepEqual(result, { scenario: "SMOKE-01", outcome: "FAIL" });
  assert.equal(report.smoke, "FAIL");
  assert.equal(report.authenticatedUat, "BLOCKED");
  assert.equal(JSON.stringify(report).includes("secret"), false);
});

test("interrupted and skipped runs cannot claim smoke success", () => {
  assert.equal(createReport("interrupted", []).smoke, "FAIL");
  assert.equal(scenarioResult({ title: "SMOKE-02" }, { status: "skipped" }).outcome, "NOT RUN");
  assert.equal(createReport("passed", []).smoke, "FAIL");
  assert.equal(createReport("passed", [{ scenario: "SMOKE-01", outcome: "PASS" }]).smoke, "PASS");
});
