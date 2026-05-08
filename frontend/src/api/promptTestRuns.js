import request from "./request";

export function getPromptTestRuns() {
  return request.get("/prompt-test-runs");
}

export function getPromptTestRunDetail(runId) {
  return request.get(`/prompt-test-runs/${runId}`);
}

export function runPromptOnce(data) {
  return request.post("/prompt-test-runs/run-once", data, {
    timeout: 300000
  });
}
