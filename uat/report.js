import { mkdirSync, writeFileSync } from "node:fs";
import { approvedOrigin } from "./safety.js";

export function scenarioResult(test, result) {
  return {
    scenario: /^SMOKE-\d{2}$/.test(test.title) ? test.title : "UNKNOWN",
    outcome: result.status === "passed" ? "PASS" : result.status === "skipped" ? "NOT RUN" : "FAIL",
  };
}

export function createReport(status, scenarios, startedAt = new Date().toISOString()) {
  return {
    startedAt,
    origin: approvedOrigin,
    runnerCommit: /^[0-9a-f]{40}$/.test(process.env.GITHUB_SHA ?? "") ? process.env.GITHUB_SHA : null,
    deployedCommit: null,
    smoke: status === "passed" && scenarios.length > 0 && scenarios.every((item) => item.outcome === "PASS") ? "PASS" : "FAIL",
    authenticatedUat: "BLOCKED",
    scenarios,
  };
}

export default class SanitizedReporter {
  scenarios = [];
  startedAt = new Date().toISOString();

  onTestEnd(test, result) {
    const scenario = scenarioResult(test, result);
    this.scenarios.push(scenario);
    console.log(`${scenario.scenario}: ${scenario.outcome}`);
  }

  onError() {
    console.error("UAT runner error; no raw exception data is published.");
  }

  onEnd(result) {
    const report = createReport(result.status, this.scenarios, this.startedAt);
    mkdirSync("results", { recursive: true });
    writeFileSync("results/smoke.json", `${JSON.stringify(report, null, 2)}\n`);
    console.log(`Smoke: ${report.smoke}; authenticated UAT: BLOCKED.`);
    if (report.smoke !== "PASS") return { status: "failed" };
  }
}
