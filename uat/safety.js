export const approvedOrigin = "https://0w4jgh9j9a.execute-api.us-west-2.amazonaws.com";

export function validateTarget(value) {
  if (value !== approvedOrigin && value !== `${approvedOrigin}/`) {
    throw new Error("Unapproved UAT target; use the documented HTTPS origin.");
  }
  return approvedOrigin;
}

export function permittedRead(url, method) {
  if (method !== "GET" && method !== "HEAD") return false;
  if (!URL.canParse(url)) return false;
  return new URL(url).origin === approvedOrigin;
}
