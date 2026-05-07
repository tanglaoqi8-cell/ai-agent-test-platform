import request from "./request";

export function createTestRun(data) {
  return request.post("/test-runs", data);
}

export function getTestRuns() {
  return request.get("/test-runs");
}

export function getTestRunResults(runId) {
  return request.get(`/test-runs/${runId}/results`);
}

export function exportTestRunCsv(runId) {
  return `/api/test-runs/${runId}/export-csv`;
}
