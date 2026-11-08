import assert from "node:assert/strict";
import { test } from "node:test";
import { approvedOrigin, validateTarget, permittedRead } from "./safety.js";

test("only the approved HTTPS origin is accepted", () => {
  assert.equal(validateTarget(approvedOrigin), approvedOrigin);
  assert.equal(validateTarget(`${approvedOrigin}/`), approvedOrigin);
  for (const value of [
    "http://0w4jgh9j9a.execute-api.us-west-2.amazonaws.com",
    "https://example.com",
    `${approvedOrigin}/case`,
    `${approvedOrigin}?secret=value`,
    `${approvedOrigin}#fragment`,
    approvedOrigin.replace("https://", "https://user:password@"),
  ]) {
    assert.throws(() => validateTarget(value), /Unapproved UAT target/);
  }
});

test("network guard allows same-origin reads only", () => {
  assert.equal(permittedRead(`${approvedOrigin}/healthz`, "GET"), true);
  assert.equal(permittedRead(`${approvedOrigin}/`, "HEAD"), true);
  assert.equal(permittedRead(`${approvedOrigin}/api/auth/login`, "POST"), false);
  assert.equal(permittedRead(`${approvedOrigin}/cases`, "DELETE"), false);
  assert.equal(permittedRead("https://example.com/", "GET"), false);
  assert.equal(permittedRead("not a URL", "GET"), false);
});
