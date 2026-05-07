import request from "./request";

export function getTestTargets() {
  return request.get("/test-targets");
}

export function getTestTargetDetail(targetId) {
  return request.get(`/test-targets/${targetId}`);
}

export function createTestTarget(data) {
  return request.post("/test-targets", data);
}
