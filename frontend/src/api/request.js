import axios from "axios";

const request = axios.create({
  baseURL: "/api",
  timeout: 30000
});

request.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error?.response?.data?.detail || error.message || "请求失败";
    return Promise.reject(new Error(message));
  }
);

export default request;
