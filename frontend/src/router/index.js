import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "../views/Dashboard.vue";
import TestTargets from "../views/TestTargets.vue";
import TestSuites from "../views/TestSuites.vue";
import TestRunCreate from "../views/TestRunCreate.vue";
import TestRunResults from "../views/TestRunResults.vue";
import PromptVersions from "../views/PromptVersions.vue";
import ModelConfigs from "../views/ModelConfigs.vue";
import PromptRunOnce from "../views/PromptRunOnce.vue";
import PromptRunResults from "../views/PromptRunResults.vue";

const routes = [
  { path: "/", name: "dashboard", component: Dashboard },
  { path: "/test-targets", name: "test-targets", component: TestTargets },
  { path: "/test-suites", name: "test-suites", component: TestSuites },
  { path: "/prompt-versions", name: "prompt-versions", component: PromptVersions },
  { path: "/model-configs", name: "model-configs", component: ModelConfigs },
  { path: "/prompt-run-once", name: "prompt-run-once", component: PromptRunOnce },
  { path: "/prompt-run-results", name: "prompt-run-results", component: PromptRunResults },
  { path: "/test-runs/create", name: "test-run-create", component: TestRunCreate },
  { path: "/test-runs/results", name: "test-run-results", component: TestRunResults }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
