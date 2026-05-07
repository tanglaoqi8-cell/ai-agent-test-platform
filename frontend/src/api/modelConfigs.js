import request from "./request";

export function getModelConfigs() {
  return request.get("/model-configs");
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
