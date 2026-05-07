<template>
  <el-space direction="vertical" fill size="large" class="full-width">
    <el-card>
      <template #header><div class="card-header">执行测试</div></template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="测试对象">
          <el-select v-model="form.target_id" class="w-100" placeholder="请选择测试对象">
            <el-option
              v-for="item in targets"
              :key="item.id"
              :label="`${item.id} - ${item.name}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="用例集">
          <el-select v-model="form.suite_id" class="w-100" placeholder="请选择用例集">
            <el-option
              v-for="item in suites"
              :key="item.id"
              :label="`${item.id} - ${item.suite_name}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-button type="primary" :loading="submitting" @click="handleRun">执行测试</el-button>
      </el-form>
    </el-card>

    <el-card v-if="runSummary">
      <template #header><div class="card-header">执行结果摘要</div></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行批次ID">{{ runSummary.run_id }}</el-descriptions-item>
        <el-descriptions-item label="总数">{{ runSummary.total }}</el-descriptions-item>
        <el-descriptions-item label="通过">{{ runSummary.passed }}</el-descriptions-item>
        <el-descriptions-item label="失败">{{ runSummary.failed }}</el-descriptions-item>
      </el-descriptions>

      <el-button class="mt-12" type="success" @click="goToResults">查看执行结果</el-button>
    </el-card>
  </el-space>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getTestTargets } from "../api/testTargets";
import { getTestSuites } from "../api/testCases";
import { createTestRun } from "../api/testRuns";

const router = useRouter();

const targets = ref([]);
const suites = ref([]);
const submitting = ref(false);
const runSummary = ref(null);

const form = reactive({
  target_id: null,
  suite_id: null
});

async function fetchOptions() {
  try {
    const [targetRes, suiteRes] = await Promise.all([getTestTargets(), getTestSuites()]);
    targets.value = Array.isArray(targetRes.data) ? targetRes.data : targetRes.data?.items || [];
    suites.value = Array.isArray(suiteRes.data) ? suiteRes.data : suiteRes.data?.items || [];
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function handleRun() {
  if (!form.target_id || !form.suite_id) {
    ElMessage.warning("请选择测试对象和用例集");
    return;
  }

  submitting.value = true;
  try {
    const { data } = await createTestRun({
      target_id: form.target_id,
      suite_id: form.suite_id
    });

    runSummary.value = {
      run_id: data?.run_id,
      total: data?.total ?? "-",
      passed: data?.passed ?? "-",
      failed: data?.failed ?? "-"
    };

    ElMessage.success("执行成功");
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    submitting.value = false;
  }
}

function goToResults() {
  router.push("/test-runs/results");
}

onMounted(fetchOptions);
</script>

<style scoped>
.full-width {
  width: 100%;
}

.card-header {
  font-weight: 600;
}

.w-100 {
  width: 100%;
}

.mt-12 {
  margin-top: 12px;
}
</style>
