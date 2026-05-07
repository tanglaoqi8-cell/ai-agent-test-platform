<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card>
        <template #header><div class="card-header">执行批次列表</div></template>
        <div class="run-search">
          <el-input
            v-model="runIdKeyword"
            clearable
            placeholder="搜索执行批次ID"
          />
        </div>

        <div class="run-stats">
          批次总数：{{ runs.length }} ｜ 当前显示：{{ filteredRuns.length }}
        </div>

        <el-table :data="filteredRuns" border v-loading="loadingRuns" @row-click="handleRunClick">
          <el-table-column prop="id" label="执行批次ID" width="110" />
          <el-table-column prop="target_id" label="测试对象ID" width="110" />
          <el-table-column prop="suite_id" label="用例集ID" width="100" />
          <el-table-column prop="created_at" label="执行时间" min-width="160" />
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button link type="primary" @click.stop="handleExport(scope.row.id)">导出 CSV</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>

    <el-col :span="16">
      <el-card>
        <template #header>
          <div class="card-header">结果详情 {{ currentRunId ? `(执行批次ID: ${currentRunId})` : "" }}</div>
        </template>

        <div class="toolbar">
          <el-button type="primary" :disabled="!currentRunId" @click="handleExportCurrent">导出当前结果 CSV</el-button>
          <el-radio-group v-model="resultFilter" size="small" class="filter-group">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="passed">只看通过</el-radio-button>
            <el-radio-button label="failed">只看失败</el-radio-button>
          </el-radio-group>
        </div>

        <div class="result-stats">
          总数：{{ totalCount }} ｜ 通过：{{ passedCount }} ｜ 失败：{{ failedCount }} ｜ 当前显示：{{ filteredResults.length }}
        </div>

        <el-card v-if="failedCount > 0 && resultFilter === 'all'" shadow="never" class="failed-summary-card">
          <template #header>
            <div class="failed-summary-header">
              <span>失败摘要</span>
              <el-button link type="danger" @click="resultFilter = 'failed'">只看失败</el-button>
            </div>
          </template>

          <div v-for="item in failedSummaryList" :key="item.case_id" class="failed-summary-item">
            <div class="failed-line"><strong>用例ID：</strong>{{ item.case_id }}</div>
            <div class="failed-line"><strong>用例名称：</strong>{{ item.case_name || "-" }}</div>
            <div class="failed-line"><strong>原因：</strong>{{ getOutputSummary(item.reason) }}</div>
          </div>

          <div v-if="failedCount > 5" class="failed-summary-tip">
            仅展示前 5 条失败用例，请使用“只看失败”查看全部
          </div>
        </el-card>

        <el-table :data="filteredResults" border v-loading="loadingResults">
          <el-table-column prop="case_id" label="用例ID" width="90" />
          <el-table-column prop="case_name" label="用例名称" min-width="120" />
          <el-table-column prop="input_text" label="输入内容" min-width="160" />
          <el-table-column label="实际输出" min-width="220">
            <template #default="scope">
              <div class="output-cell">
                <span class="output-summary">{{ getOutputSummary(scope.row.actual_output) }}</span>
                <div class="output-action">
                  <el-button link type="primary" @click="showOutputDialog(scope.row.actual_output)">查看详情</el-button>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="assert_type" label="断言类型" width="110" />
          <el-table-column prop="expected_value" label="期望值" min-width="150" />
          <el-table-column label="是否通过" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.passed ? 'success' : 'danger'">{{ scope.row.passed ? "通过" : "失败" }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="原因" min-width="220">
            <template #default="scope">
              <div class="output-cell">
                <span class="output-summary">{{ getOutputSummary(scope.row.reason) }}</span>
                <div class="output-action">
                  <el-button link type="primary" @click="showReasonDialog(scope.row.reason)">查看原因</el-button>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="latency_ms" label="耗时(ms)" width="110" />
        </el-table>
      </el-card>
    </el-col>
  </el-row>

  <el-dialog v-model="outputDialogVisible" :title="dialogTitle" width="70%">
    <pre class="output-pre">{{ formattedOutput }}</pre>
    <template #footer>
      <el-button @click="handleCopyOutput">复制内容</el-button>
      <el-button type="primary" @click="outputDialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { exportTestRunCsv, getTestRuns, getTestRunResults } from "../api/testRuns";

const runs = ref([]);
const results = ref([]);
const currentRunId = ref(null);
const loadingRuns = ref(false);
const loadingResults = ref(false);
const outputDialogVisible = ref(false);
const formattedOutput = ref("");
const dialogTitle = ref("响应详情");
const resultFilter = ref("all");
const runIdKeyword = ref("");

const filteredRuns = computed(() => {
  const keyword = runIdKeyword.value.trim();
  if (!keyword) {
    return runs.value;
  }
  return runs.value.filter((item) => String(item.id ?? "").includes(keyword));
});

const totalCount = computed(() => results.value.length);
const passedCount = computed(() => results.value.filter((item) => item.passed === true).length);
const failedCount = computed(() => results.value.filter((item) => item.passed === false).length);
const failedSummaryList = computed(() => results.value.filter((item) => item.passed === false).slice(0, 5));
const filteredResults = computed(() => {
  if (resultFilter.value === "passed") {
    return results.value.filter((item) => item.passed === true);
  }
  if (resultFilter.value === "failed") {
    return results.value.filter((item) => item.passed === false);
  }
  return results.value;
});

async function fetchRuns() {
  loadingRuns.value = true;
  try {
    const { data } = await getTestRuns();
    runs.value = Array.isArray(data) ? data : data?.items || [];
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loadingRuns.value = false;
  }
}

async function handleRunClick(row) {
  currentRunId.value = row.id;
  resultFilter.value = "all";
  loadingResults.value = true;
  try {
    const { data } = await getTestRunResults(row.id);
    results.value = Array.isArray(data) ? data : data?.items || [];
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loadingResults.value = false;
  }
}

function handleExport(runId) {
  try {
    if (!runId) {
      ElMessage.warning("无效的执行批次ID");
      return;
    }
    window.open(exportTestRunCsv(runId), "_blank");
  } catch (error) {
    ElMessage.error(error.message || "CSV 下载失败");
  }
}

function handleExportCurrent() {
  if (!currentRunId.value) {
    ElMessage.warning("请先选择一个执行批次");
    return;
  }
  handleExport(currentRunId.value);
}

function getOutputSummary(actualOutput) {
  const text = typeof actualOutput === "string" ? actualOutput : String(actualOutput ?? "");
  return text.length <= 80 ? text : `${text.slice(0, 80)}...`;
}

function showOutputDialog(actualOutput) {
  dialogTitle.value = "实际输出详情";
  showContentDialog(actualOutput);
}

function showReasonDialog(reasonText) {
  dialogTitle.value = "原因详情";
  showContentDialog(reasonText);
}

function showContentDialog(rawText) {
  const text = typeof rawText === "string" ? rawText : String(rawText ?? "");
  try {
    formattedOutput.value = JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    formattedOutput.value = text;
  }
  outputDialogVisible.value = true;
}

async function handleCopyOutput() {
  try {
    await navigator.clipboard.writeText(formattedOutput.value || "");
    ElMessage.success("已复制");
  } catch (error) {
    ElMessage.error(error.message || "复制失败");
  }
}

onMounted(fetchRuns);
</script>

<style scoped>
.card-header {
  font-weight: 600;
}

.run-search {
  margin-bottom: 8px;
}

.run-stats {
  margin-bottom: 12px;
  color: #4b5563;
  font-size: 13px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.filter-group {
  flex-shrink: 0;
}

.result-stats {
  margin-bottom: 12px;
  color: #4b5563;
  font-size: 13px;
}

.failed-summary-card {
  margin-bottom: 12px;
}

.failed-summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.failed-summary-item {
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 6px;
  background: #fff7f7;
  border: 1px solid #fde2e2;
}

.failed-line {
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}

.failed-summary-tip {
  color: #b45309;
  font-size: 12px;
}

.output-cell {
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.output-summary {
  padding: 8px 10px;
  font-family: Consolas, "Courier New", monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #374151;
  background: #f3f4f6;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.output-action {
  margin-top: 6px;
  text-align: left;
}

.output-pre {
  margin: 0;
  padding: 12px;
  max-height: 60vh;
  overflow: auto;
  white-space: pre;
  font-family: Consolas, "Courier New", monospace;
  background: #f5f7fa;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
}
</style>
