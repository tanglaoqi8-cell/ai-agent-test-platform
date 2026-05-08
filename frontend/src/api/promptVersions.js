import request from "./request";

export function getPromptVersions(params) {
  return request.get("/prompt-versions", { params });
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

export function updatePromptVersionStatus(promptVersionId, status) {
  return request.put(`/prompt-versions/${promptVersionId}/status`, { status });
}

export function deletePromptVersion(promptVersionId) {
  return request.delete(`/prompt-versions/${promptVersionId}`);
}
