import request from "./request";

export function getPromptVersions() {
  return request.get("/prompt-versions");
}

export function getPromptVersionDetail(promptVersionId) {
  return request.get(`/prompt-versions/${promptVersionId}`);
}

export function createPromptVersion(data) {
  return request.post("/prompt-versions", data);
}

export function updatePromptVersion(promptVersionId, data) {
  return request.put(`/prompt-versions/${promptVersionId}`, data);
}
