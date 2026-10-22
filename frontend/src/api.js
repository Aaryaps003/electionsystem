const ADMIN_KEY = "election_admin_token";
const VOTER_KEY = "election_voter_token";

export const getToken = () => localStorage.getItem(ADMIN_KEY);
export const setToken = (t) => localStorage.setItem(ADMIN_KEY, t);
export const clearToken = () => localStorage.removeItem(ADMIN_KEY);

// Voter sessions live in sessionStorage so they end when the tab closes.
export const getVoterToken = () => sessionStorage.getItem(VOTER_KEY);
export const setVoterToken = (t) => sessionStorage.setItem(VOTER_KEY, t);
export const clearVoterToken = () => sessionStorage.removeItem(VOTER_KEY);

function errorMessage(data, fallback) {
  if (!data) return fallback;
  if (typeof data.error === "string") return data.error;
  if (typeof data.detail === "string") return data.detail;
  // DRF field errors: { prn: ["..."], ... }
  const first = Object.entries(data)[0];
  if (first) return `${first[0]}: ${[].concat(first[1]).join(" ")}`;
  return fallback;
}

/** auth: "admin" | "voter" | false */
export async function api(path, { method = "GET", body, auth = false } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (auth === "admin" && getToken()) headers["Authorization"] = `Token ${getToken()}`;
  if (auth === "voter" && getVoterToken()) headers["Authorization"] = `Bearer ${getVoterToken()}`;

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(errorMessage(data, `Request failed (${res.status})`));
    err.status = res.status;
    throw err;
  }
  return data;
}

export async function downloadResultsXml() {
  const res = await fetch("/api/admin/export/", {
    headers: { Authorization: `Token ${getToken()}` },
  });
  if (!res.ok) {
    const err = new Error("Export failed. Please log in again.");
    err.status = res.status;
    throw err;
  }
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = "results.xml";
  a.click();
  URL.revokeObjectURL(url);
}
