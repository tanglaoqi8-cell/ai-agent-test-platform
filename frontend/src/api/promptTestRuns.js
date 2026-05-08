import request from "./request";

export function runPromptOnce(data) {
  return request.post("/prompt-test-runs/run-once", data, {
    timeout: 300000
  });
}
