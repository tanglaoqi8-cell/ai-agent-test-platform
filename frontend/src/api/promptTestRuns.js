import request from "./request";

export function getPromptTestRuns() {
  return request.get("/prompt-test-runs");
}

export function getPromptTestRunDetail(runId) {
  return request.get(`/prompt-test-runs/${runId}`);
}

export function scorePromptTestRun(runId, data) {
  return request.post(`/prompt-test-runs/${runId}/score`, data, {
    timeout: 300000
  });
}

export function createPromptManualReview(runId, data) {
  return request.post(`/prompt-test-runs/${runId}/manual-review`, data);
}

export function getPromptTestRunScores(runId) {
  return request.get(`/prompt-test-runs/${runId}/scores`);
}

export function getPromptManualReviews(runId) {
  return request.get(`/prompt-test-runs/${runId}/manual-reviews`);
}

export function runPromptOnce(data) {
  return request.post("/prompt-test-runs/run-once", data, {
    timeout: 300000
  });
}

export function runPromptRepeat(data) {
  return request.post("/prompt-test-runs/run-repeat", data, {
    timeout: 300000
  });
}
