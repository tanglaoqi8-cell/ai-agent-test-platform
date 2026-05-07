import request from "./request";

export function uploadTestCases(formData) {
  return request.post("/test-cases/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
}

export function getTestSuites() {
  return request.get("/test-suites");
}

export function getSuiteCases(suiteId) {
  return request.get(`/test-suites/${suiteId}/cases`);
}
