<template>
  <el-space direction="vertical" fill size="large" class="full-width">
    <el-card>
      <template #header>
        <div class="header-row">
          <span class="page-title">Prompt 执行记录</span>
          <div class="actions">
            <el-input v-model="runIdKeyword" placeholder="搜索执行批次ID" clearable class="search-input" />
            <el-select v-model="statusFilter" class="status-select">
              <el-option label="全部" value="all" />
              <el-option label="success" value="success" />
              <el-option label="failed" value="failed" />
              <el-option label="running" value="running" />
            </el-select>
            <el-button @click="fetchRuns">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredRuns" border v-loading="listLoading">
        <el-table-column label="执行批次ID" width="100">
          <template #default="scope">{{ resolveRunId(scope.row) }}</template>
        </el-table-column>
        <el-table-column label="执行状态" width="110">
          <template #default="scope">
            <el-tag :type="statusTagType(resolveStatus(scope.row))">{{ resolveStatus(scope.row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Prompt版本ID" width="140">
          <template #default="scope">{{ resolveField(scope.row, ["prompt_version_id"]) }}</template>
        </el-table-column>
        <el-table-column label="模型配置ID" width="130">
          <template #default="scope">{{ resolveField(scope.row, ["model_config_id"]) }}</template>
        </el-table-column>
        <el-table-column label="开始时间" min-width="160">
          <template #default="scope">{{ formatDateTimeToChina(resolveField(scope.row, ["started_at", "created_at"])) }}</template>
        </el-table-column>
        <el-table-column label="结束时间" min-width="160">
          <template #default="scope">{{ formatDateTimeToChina(resolveField(scope.row, ["finished_at", "updated_at"])) }}</template>
        </el-table-column>
        <el-table-column label="耗时(ms)" width="110">
          <template #default="scope">{{ resolveField(scope.row, ["duration_ms"]) }}</template>
        </el-table-column>
        <el-table-column label="错误信息" min-width="180" show-overflow-tooltip>
          <template #default="scope">{{ resolveField(scope.row, ["error_message", "message", "reason"]) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openDetail(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailVisible" :title="`Prompt 执行详情 - 执行批次ID ${detailRunId || '-'}`" width="80%" @closed="closeDetail">
      <div v-loading="detailLoading">
        <template v-if="detailData">
          <div class="section-title">基本信息</div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="执行批次ID">{{ normalizedRunBasicInfo.run_id }}</el-descriptions-item>
            <el-descriptions-item label="执行状态">{{ normalizedRunBasicInfo.status }}</el-descriptions-item>
            <el-descriptions-item label="Prompt版本ID">{{ normalizedRunBasicInfo.prompt_version_id }}</el-descriptions-item>
            <el-descriptions-item label="模型配置ID">{{ normalizedRunBasicInfo.model_config_id }}</el-descriptions-item>
            <el-descriptions-item label="开始时间">{{ formatDateTimeToChina(normalizedRunBasicInfo.started_at) }}</el-descriptions-item>
            <el-descriptions-item label="结束时间">{{ formatDateTimeToChina(normalizedRunBasicInfo.finished_at) }}</el-descriptions-item>
            <el-descriptions-item label="耗时(ms)">{{ normalizedRunBasicInfo.duration_ms }}</el-descriptions-item>
            <el-descriptions-item label="错误信息" :span="2">{{ normalizedRunBasicInfo.error_message }}</el-descriptions-item>
          </el-descriptions>

          <div class="section-title">执行结果</div>
          <el-table v-if="normalizedResults.length > 1" :data="normalizedResults" border>
            <el-table-column prop="result_id" label="结果ID" width="100" />
            <el-table-column prop="repeat_index" label="重复序号" width="110" />
            <el-table-column prop="status" label="执行状态" width="100" />
            <el-table-column prop="duration_ms" label="耗时(ms)" width="110" />
            <el-table-column prop="error_message" label="错误信息" min-width="180" show-overflow-tooltip />
            <el-table-column label="实际输出" min-width="220" show-overflow-tooltip>
              <template #default="scope">{{ summarizeOutput(scope.row.actual_output) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="scope">
                <el-button link type="primary" @click="openOutputDialog(scope.row.actual_output)">查看完整输出</el-button>
              </template>
            </el-table-column>
          </el-table>

          <template v-else>
            <div class="single-result" v-if="normalizedResults.length === 1">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="结果ID">{{ normalizedResults[0].result_id || '-' }}</el-descriptions-item>
                <el-descriptions-item label="执行状态">{{ normalizedResults[0].status || '-' }}</el-descriptions-item>
                <el-descriptions-item label="耗时(ms)">{{ normalizedResults[0].duration_ms ?? '-' }}</el-descriptions-item>
                <el-descriptions-item label="错误信息">{{ normalizedResults[0].error_message || '-' }}</el-descriptions-item>
              </el-descriptions>
              <div class="block-label">实际输出</div>
              <pre class="long-block">{{ formatMaybeJson(normalizedResults[0].actual_output) }}</pre>
            </div>
            <el-empty v-else description="暂无执行结果" />
          </template>

          <div class="section-title">断言结果</div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="断言类型">{{ normalizedAssertion.assertType }}</el-descriptions-item>
            <el-descriptions-item label="期望值">{{ normalizedAssertion.expectedValue }}</el-descriptions-item>
            <el-descriptions-item label="断言结果">
              <el-tag :type="normalizedAssertion.tagType">{{ normalizedAssertion.statusText }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="断言状态">{{ normalizedAssertion.rawStatus }}</el-descriptions-item>
            <el-descriptions-item label="信息 / 原因" :span="2">{{ normalizedAssertion.message }}</el-descriptions-item>
          </el-descriptions>

          <div class="section-title">输入快照</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="输入文本">{{ resolvedSnapshot.input_text || '-' }}</el-descriptions-item>
            <el-descriptions-item label="输入变量">
              <pre class="long-block small">{{ formatMaybeJson(resolvedSnapshot.input_variables) }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="渲染后Prompt">
              <pre class="long-block small">{{ resolvedSnapshot.rendered_prompt || '-' }}</pre>
            </el-descriptions-item>
          </el-descriptions>

          <div class="section-title">LLM 自动评分</div>
          <template v-if="latestScore">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="总分">{{ resolveField(latestScore, ["total_score", "score"]) }}</el-descriptions-item>
              <el-descriptions-item label="评分状态">{{ resolveField(latestScore, ["status"]) }}</el-descriptions-item>
              <el-descriptions-item label="维度评分" :span="2">
                <pre class="long-block small">{{ formatMaybeJson(resolveField(latestScore, ["dimension_scores"])) }}</pre>
              </el-descriptions-item>
              <el-descriptions-item label="评分理由" :span="2">{{ resolveField(latestScore, ["score_reason", "reason"]) }}</el-descriptions-item>
              <el-descriptions-item label="问题点" :span="2">{{ resolveField(latestScore, ["problem_points"]) }}</el-descriptions-item>
              <el-descriptions-item label="优化建议" :span="2">{{ resolveField(latestScore, ["suggestion"]) }}</el-descriptions-item>
              <el-descriptions-item label="错误信息" :span="2">{{ resolveField(latestScore, ["error_message"]) }}</el-descriptions-item>
              <el-descriptions-item label="评分时间">{{ formatDateTimeToChina(resolveField(latestScore, ["created_at", "updated_at"])) }}</el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty v-else description="暂无 LLM 自动评分" />

          <div class="section-title">人工复核</div>
          <template v-if="latestManualReview">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="人工判定">{{ resolveField(latestManualReview, ["manual_status", "status"]) }}</el-descriptions-item>
              <el-descriptions-item label="复核人">{{ resolveField(latestManualReview, ["reviewer"]) }}</el-descriptions-item>
              <el-descriptions-item label="人工备注" :span="2">{{ resolveField(latestManualReview, ["manual_remark", "remark"]) }}</el-descriptions-item>
              <el-descriptions-item label="复核时间">{{ formatDateTimeToChina(resolveField(latestManualReview, ["created_at", "updated_at"])) }}</el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty v-else description="暂无人工复核记录" />
        </template>
      </div>
    </el-dialog>

    <el-dialog v-model="outputDialogVisible" title="完整输出" width="70%">
      <pre class="long-block">{{ outputDialogText }}</pre>
      <template #footer>
        <el-button type="primary" @click="outputDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </el-space>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { getPromptTestRunDetail, getPromptTestRuns } from "../api/promptTestRuns";
import { formatDateTimeToChina } from "../utils/time";

const listLoading = ref(false);
const detailLoading = ref(false);
const runs = ref([]);
const detailData = ref(null);
const detailVisible = ref(false);
const detailRunId = ref(null);
const runIdKeyword = ref("");
const statusFilter = ref("all");
const outputDialogVisible = ref(false);
const outputDialogText = ref("");

const filteredRuns = computed(() => {
  const keyword = runIdKeyword.value.trim();
  return runs.value.filter((item) => {
    const runId = String(resolveRunId(item));
    const status = String(resolveStatus(item)).toLowerCase();
    const hitKeyword = !keyword || runId.includes(keyword);
    const hitStatus = statusFilter.value === "all" || status === statusFilter.value;
    return hitKeyword && hitStatus;
  });
});

const normalizedResults = computed(() => {
  if (!detailData.value) return [];
  const data = detailData.value;
  if (Array.isArray(data.results)) {
    return data.results.map((item, index) => normalizeResultItem(item, index));
  }
  if (data.result && typeof data.result === "object") {
    return [normalizeResultItem(data.result, 0)];
  }
  return [];
});

const normalizedAssertion = computed(() => normalizeAssertion(detailData.value));

const resolvedSnapshot = computed(() => {
  const data = detailData.value || {};
  const snapshot = data.input_snapshot || {};
  return {
    input_text: snapshot.input_text ?? data.input_text ?? "",
    input_variables: snapshot.input_variables ?? data.input_variables ?? null,
    rendered_prompt: snapshot.rendered_prompt ?? data.rendered_prompt ?? ""
  };
});

const latestScore = computed(() => detailData.value?.latest_score || null);
const latestManualReview = computed(() => detailData.value?.latest_manual_review || null);
const normalizedRunBasicInfo = computed(() => normalizeRunBasicInfo(detailData.value));

function resolveRunId(item) {
  return item?.run_id ?? item?.id ?? "-";
}

function resolveStatus(item) {
  return item?.status || item?.run_status || item?.run?.status || item?.run_info?.status || "-";
}

function resolveField(item, keys) {
  if (!item) return "-";
  for (const key of keys) {
    const value = item[key];
    if (value !== undefined && value !== null && value !== "") {
      return value;
    }
  }
  return "-";
}

function statusTagType(status) {
  const s = String(status).toLowerCase();
  if (s === "success" || s === "passed") return "success";
  if (s === "failed" || s === "fail" || s === "error") return "danger";
  if (s === "running") return "warning";
  return "info";
}

function normalizeResultItem(item, index) {
  return {
    result_id: item?.result_id ?? item?.id ?? index + 1,
    repeat_index: item?.repeat_index ?? item?.index ?? "-",
    status: item?.status || "-",
    duration_ms: item?.duration_ms ?? "-",
    error_message: item?.error_message || item?.message || item?.reason || "-",
    actual_output: item?.actual_output ?? item?.output ?? ""
  };
}

function summarizeOutput(value) {
  const text = formatMaybeJson(value);
  return text.length > 120 ? `${text.slice(0, 120)}...` : text;
}

function formatMaybeJson(value) {
  if (value === undefined || value === null || value === "") return "-";
  if (typeof value === "object") {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }
  const text = String(value);
  try {
    return JSON.stringify(JSON.parse(text), null, 2);
  } catch {
    return text;
  }
}

function openOutputDialog(value) {
  outputDialogText.value = formatMaybeJson(value);
  outputDialogVisible.value = true;
}

function normalizeStatusValue(value) {
  if (value === true) return "passed";
  if (value === false) return "failed";
  if (typeof value === "string") {
    const v = value.trim().toLowerCase();
    if (["passed", "pass", "success", "ok", "true"].includes(v)) return "passed";
    if (["failed", "fail", "error", "false"].includes(v)) return "failed";
    if (["skipped", "skip"].includes(v)) return "skipped";
  }
  return "";
}

function normalizeAssertion(data) {
  const source = data || {};
  const assertion = source.assertion || source.assertion_result || null;

  const assertType =
    assertion?.assert_type ||
    assertion?.type ||
    source?.assert_type ||
    (source?.result && source.result.assert_type) ||
    "";
  const expectedValue =
    assertion?.expected_value ??
    assertion?.expected ??
    source?.expected_value ??
    (source?.result && source.result.expected_value) ??
    "";
  const rawStatus =
    assertion?.passed ??
    assertion?.is_passed ??
    assertion?.assertion_passed ??
    assertion?.pass ??
    assertion?.status ??
    assertion?.result ??
    source?.assertion_passed;
  const message =
    assertion?.message ||
    assertion?.reason ||
    assertion?.error_message ||
    source?.assertion_message ||
    source?.reason ||
    source?.error_message ||
    "";

  if (!assertType && rawStatus === undefined) {
    return {
      assertType: "不启用",
      expectedValue: "-",
      statusText: "不启用",
      rawStatus: "-",
      message: "暂无断言结果",
      tagType: "info"
    };
  }

  const normalized = normalizeStatusValue(rawStatus);
  if (normalized === "passed") {
    return {
      assertType: assertType || "-",
      expectedValue: expectedValue === "" ? "-" : expectedValue,
      statusText: "通过",
      rawStatus: rawStatus === undefined ? "-" : String(rawStatus),
      message: message || "-",
      tagType: "success"
    };
  }
  if (normalized === "failed") {
    return {
      assertType: assertType || "-",
      expectedValue: expectedValue === "" ? "-" : expectedValue,
      statusText: "失败",
      rawStatus: rawStatus === undefined ? "-" : String(rawStatus),
      message: message || "-",
      tagType: "danger"
    };
  }
  if (normalized === "skipped") {
    return {
      assertType: assertType || "-",
      expectedValue: expectedValue === "" ? "-" : expectedValue,
      statusText: "跳过",
      rawStatus: rawStatus === undefined ? "-" : String(rawStatus),
      message: message || "-",
      tagType: "warning"
    };
  }

  return {
    assertType: assertType || "-",
    expectedValue: expectedValue === "" ? "-" : expectedValue,
    statusText: "未返回断言结果",
    rawStatus: rawStatus === undefined ? "-" : String(rawStatus),
    message: message || "未返回断言结果",
    tagType: "warning"
  };
}

function normalizeRunBasicInfo(detail) {
  const d = detail || {};
  return {
    run_id:
      d?.run_id ??
      d?.id ??
      d?.run?.id ??
      d?.run_info?.id ??
      "-",
    status:
      d?.status ??
      d?.run_status ??
      d?.run?.status ??
      d?.run_info?.status ??
      "-",
    prompt_version_id:
      d?.prompt_version_id ??
      d?.run?.prompt_version_id ??
      d?.run_info?.prompt_version_id ??
      "-",
    model_config_id:
      d?.model_config_id ??
      d?.run?.model_config_id ??
      d?.run_info?.model_config_id ??
      "-",
    started_at:
      d?.started_at ??
      d?.created_at ??
      d?.run?.started_at ??
      d?.run?.created_at ??
      d?.run_info?.started_at ??
      d?.run_info?.created_at ??
      "-",
    finished_at:
      d?.finished_at ??
      d?.updated_at ??
      d?.run?.finished_at ??
      d?.run?.updated_at ??
      d?.run_info?.finished_at ??
      d?.run_info?.updated_at ??
      "-",
    duration_ms:
      d?.duration_ms ??
      d?.run?.duration_ms ??
      d?.run_info?.duration_ms ??
      "-",
    error_message:
      d?.error_message ??
      d?.run?.error_message ??
      d?.run_info?.error_message ??
      d?.message ??
      d?.reason ??
      "-"
  };
}

async function fetchRuns() {
  listLoading.value = true;
  try {
    const { data } = await getPromptTestRuns();
    runs.value = Array.isArray(data) ? data : data?.items || [];
  } catch (error) {
    ElMessage.error(error.message || "获取 Prompt 执行记录失败");
  } finally {
    listLoading.value = false;
  }
}

async function openDetail(row) {
  const runId = resolveRunId(row);
  if (runId === "-") {
    ElMessage.warning("无效的执行批次ID");
    return;
  }

  detailVisible.value = true;
  detailLoading.value = true;
  detailRunId.value = runId;
  detailData.value = null;

  try {
    const { data } = await getPromptTestRunDetail(runId);
    detailData.value = data;
  } catch (error) {
    ElMessage.error(error.message || "获取执行详情失败");
    detailVisible.value = false;
  } finally {
    detailLoading.value = false;
  }
}

function closeDetail() {
  detailData.value = null;
  detailRunId.value = null;
  detailLoading.value = false;
}

onMounted(fetchRuns);
</script>

<style scoped>
.full-width {
  width: 100%;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-title {
  font-weight: 600;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  width: 180px;
}

.status-select {
  width: 120px;
}

.section-title {
  margin: 14px 0 8px;
  font-weight: 600;
}

.block-label {
  margin: 10px 0 6px;
  color: #374151;
}

.long-block {
  margin: 0;
  padding: 12px;
  max-height: 240px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
}

.long-block.small {
  max-height: 200px;
}

.single-result {
  margin-bottom: 8px;
}
</style>
