import request from "./request";

export function getModelConfigs(params) {
  return request.get("/model-configs", { params });
}

export function getModelConfigDetail(modelConfigId) {
  return request.get(`/model-configs/${modelConfigId}`);
}

export function createModelConfig(data) {
  return request.post("/model-configs", data);
}

export function updateModelConfig(modelConfigId, data) {
  return request.put(`/model-configs/${modelConfigId}`, data);
}

export function updateModelConfigStatus(modelConfigId, status) {
  return request.put(`/model-configs/${modelConfigId}/status`, { status });
}

export function deleteModelConfig(modelConfigId) {
  return request.delete(`/model-configs/${modelConfigId}`);
}
