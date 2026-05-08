<template>
  <el-space direction="vertical" fill size="large" class="full-width">
    <el-card>
      <template #header>
        <div class="header-row">
          <span class="page-title">Prompt 单轮执行</span>
        </div>
      </template>

      <el-form :model="formModel" :rules="formRules" ref="formRef" label-width="130px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="Prompt 版本" prop="prompt_version_id">
              <el-select v-model="formModel.prompt_version_id" class="w-100" placeholder="请选择 Prompt 版本" :loading="optionsLoading">
                <el-option
                  v-for="item in promptVersions"
                  :key="item.id"
                  :label="`${item.id} - ${item.prompt_name || '-'} - ${item.version || '-'}`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模型配置" prop="model_config_id">
              <el-select v-model="formModel.model_config_id" class="w-100" placeholder="请选择模型配置" :loading="optionsLoading">
                <el-option
                  v-for="item in modelConfigs"
                  :key="item.id"
                  :label="`${item.id} - ${item.config_name || '-'} - ${item.model || '-'}`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="输入内容" prop="input_text">
          <el-input v-model="formModel.input_text" type="textarea" :rows="5" placeholder="请输入本次测试输入内容" />
        </el-form-item>

        <el-form-item label="变量 JSON">
          <el-input v-model="formModel.input_variables_text" type="textarea" :rows="4" placeholder='可选，示例：{"product_name":"智能台灯"}' />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="断言类型">
              <el-select v-model="formModel.assert_type" class="w-100" placeholder="不启用断言">
                <el-option label="不启用断言" value="" />
                <el-option label="contains" value="contains" />
                <el-option label="regex" value="regex" />
                <el-option label="json_valid" value="json_valid" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="期望值">
              <el-input
                v-model="formModel.expected_value"
                :disabled="isExpectedValueDisabled"
                :placeholder="expectedValuePlaceholder"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" :loading="runLoading" @click="handleRun">执行</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="runResult">
      <template #header>
        <div class="header-row">
          <span class="page-title">执行结果</span>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="run_id">{{ runResult.run_id ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="result_id">{{ runResult.result_id ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="status">{{ runResult.status ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="prompt_version_id">{{ runResult.prompt_version_id ?? formModel.prompt_version_id ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="model_config_id">{{ runResult.model_config_id ?? formModel.model_config_id ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="duration_ms">{{ runResult.duration_ms ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="error_message" :span="2">{{ runResult.error_message || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="block-title">实际输出</div>
      <pre class="output-block">{{ formatMaybeJson(runResult.actual_output) }}</pre>

      <div class="block-title">断言结果</div>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="是否通过">
          <el-tag :type="normalizedAssertion.tagType">{{ normalizedAssertion.statusText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="assert_type">{{ normalizedAssertion.assertType }}</el-descriptions-item>
        <el-descriptions-item label="expected_value" :span="2">{{ normalizedAssertion.expectedValue }}</el-descriptions-item>
        <el-descriptions-item label="message / reason" :span="2">{{ normalizedAssertion.message }}</el-descriptions-item>
      </el-descriptions>

      <div class="block-title">input_snapshot</div>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="input_text">{{ resolveSnapshot(runResult).input_text || '-' }}</el-descriptions-item>
        <el-descriptions-item label="input_variables">
          <pre class="output-block small">{{ formatMaybeJson(resolveSnapshot(runResult).input_variables) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="rendered_prompt">
          <pre class="output-block small">{{ resolveSnapshot(runResult).rendered_prompt || '-' }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never">
      <div class="tips-title">使用提示</div>
      <div class="tips-line">1. input_variables 必须是合法 JSON 对象。</div>
      <div class="tips-line">2. contains / regex 需要填写 expected_value。</div>
      <div class="tips-line">3. json_valid 不需要填写 expected_value。</div>
    </el-card>
  </el-space>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { getPromptVersions } from "../api/promptVersions";
import { getModelConfigs } from "../api/modelConfigs";
import { runPromptOnce } from "../api/promptTestRuns";

const optionsLoading = ref(false);
const runLoading = ref(false);
const promptVersions = ref([]);
const modelConfigs = ref([]);
const runResult = ref(null);
const lastRunAssertionConfig = ref({
  assert_type: "",
  expected_value: ""
});
const formRef = ref(null);

const createInitialForm = () => ({
  prompt_version_id: null,
  model_config_id: null,
  input_text: "",
  input_variables_text: "",
  assert_type: "",
  expected_value: ""
});

const formModel = reactive(createInitialForm());

const formRules = {
  prompt_version_id: [{ required: true, message: "请选择 Prompt 版本", trigger: "change" }],
  model_config_id: [{ required: true, message: "请选择模型配置", trigger: "change" }],
  input_text: [{ required: true, message: "请输入输入内容", trigger: "blur" }]
};

const isExpectedValueDisabled = computed(
  () => formModel.assert_type === "json_valid" || !formModel.assert_type
);

const expectedValuePlaceholder = computed(() => {
  if (formModel.assert_type === "json_valid") return "json_valid 不需要填写期望值";
  if (!formModel.assert_type) return "未启用断言";
  return "contains/regex 时必填";
});

function normalizeList(data) {
  return Array.isArray(data) ? data : data?.items || [];
}

watch(
  () => formModel.assert_type,
  (newType, oldType) => {
    const fromContainsOrRegex = oldType === "contains" || oldType === "regex";
    const toNoExpectedValue = newType === "json_valid" || !newType;
    if (fromContainsOrRegex && toNoExpectedValue) {
      formModel.expected_value = "";
    }
  }
);

async function fetchOptions() {
  optionsLoading.value = true;
  try {
    const [promptRes, modelRes] = await Promise.all([getPromptVersions(), getModelConfigs()]);
    promptVersions.value = normalizeList(promptRes.data);
    modelConfigs.value = normalizeList(modelRes.data);
  } catch (error) {
    ElMessage.error(error.message || "加载下拉数据失败");
  } finally {
    optionsLoading.value = false;
  }
}

function parseInputVariables() {
  const raw = (formModel.input_variables_text || "").trim();
  if (!raw) return null;

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error("input_variables 必须是合法 JSON");
  }

  if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("input_variables 必须是 JSON 对象");
  }

  return parsed;
}

function buildRunPayload(inputVariables) {
  const payload = {
    prompt_version_id: formModel.prompt_version_id,
    model_config_id: formModel.model_config_id,
    input_text: formModel.input_text
  };

  if (inputVariables) {
    payload.input_variables = inputVariables;
  }

  if (formModel.assert_type) {
    payload.assert_type = formModel.assert_type;
  }

  if (formModel.assert_type === "contains" || formModel.assert_type === "regex") {
    payload.expected_value = formModel.expected_value;
  }

  return payload;
}

async function handleRun() {
  if (!formRef.value) return;
  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  if ((formModel.assert_type === "contains" || formModel.assert_type === "regex") && !formModel.expected_value.trim()) {
    ElMessage.warning("contains/regex 断言时必须填写期望值");
    return;
  }

  let inputVariables = null;
  try {
    inputVariables = parseInputVariables();
  } catch (error) {
    ElMessage.error(error.message || "input_variables 校验失败");
    return;
  }

  runLoading.value = true;
  try {
    const payload = buildRunPayload(inputVariables);
    lastRunAssertionConfig.value = {
      assert_type: payload.assert_type || "",
      expected_value: payload.expected_value || ""
    };
    const { data } = await runPromptOnce(payload);
    runResult.value = data;
    ElMessage.success("执行成功");
  } catch (error) {
    const message = error.message || "执行失败";
    if (String(message).toLowerCase().includes("timeout")) {
      ElMessage.error("模型执行时间较长，请稍后重试或检查后端/模型服务状态。");
    } else {
      ElMessage.error(message);
    }
  } finally {
    runLoading.value = false;
  }
}

function handleReset() {
  Object.assign(formModel, createInitialForm());
  formRef.value?.clearValidate();
  runResult.value = null;
  lastRunAssertionConfig.value = {
    assert_type: "",
    expected_value: ""
  };
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

const normalizedAssertion = computed(() => normalizeAssertion(runResult.value, lastRunAssertionConfig.value));

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

function normalizeAssertion(data, requestConfig) {
  const assertion = data?.assertion || data?.assertion_result || null;
  const requestAssertType = requestConfig?.assert_type || "";
  const requestExpectedValue = requestConfig?.expected_value || "";

  const assertType =
    assertion?.assert_type ||
    assertion?.type ||
    data?.assert_type ||
    requestAssertType ||
    "";
  const expectedValue =
    assertion?.expected_value ??
    assertion?.expected ??
    data?.expected_value ??
    requestExpectedValue ??
    "";
  const message =
    assertion?.message ||
    assertion?.reason ||
    assertion?.error_message ||
    data?.assertion_message ||
    data?.reason ||
    data?.error_message ||
    "";

  if (!assertType) {
    return {
      statusText: "不启用",
      tagType: "info",
      assertType: "-",
      expectedValue: "-",
      message: "-"
    };
  }

  const statusRaw =
    assertion?.passed ??
    assertion?.is_passed ??
    assertion?.assertion_passed ??
    assertion?.pass ??
    assertion?.status ??
    assertion?.result ??
    data?.assertion_passed ??
    data?.passed;
  const normalized = normalizeStatusValue(statusRaw);

  if (normalized === "passed") {
    return {
      statusText: "通过",
      tagType: "success",
      assertType,
      expectedValue: expectedValue === "" ? "-" : expectedValue,
      message: message || "-"
    };
  }
  if (normalized === "failed") {
    return {
      statusText: "失败",
      tagType: "danger",
      assertType,
      expectedValue: expectedValue === "" ? "-" : expectedValue,
      message: message || "-"
    };
  }
  if (normalized === "skipped") {
    return {
      statusText: "跳过",
      tagType: "warning",
      assertType,
      expectedValue: expectedValue === "" ? "-" : expectedValue,
      message: message || "-"
    };
  }

  return {
    statusText: "未返回断言结果",
    tagType: "warning",
    assertType,
    expectedValue: expectedValue === "" ? "-" : expectedValue,
    message: message || "未返回断言结果"
  };
}

function resolveSnapshot(data) {
  const snapshot = data?.input_snapshot || {};
  return {
    input_text: snapshot?.input_text ?? data?.input_text ?? "",
    input_variables: snapshot?.input_variables ?? data?.input_variables ?? null,
    rendered_prompt: snapshot?.rendered_prompt ?? data?.rendered_prompt ?? ""
  };
}

onMounted(fetchOptions);
</script>

<style scoped>
.full-width {
  width: 100%;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  font-weight: 600;
}

.w-100 {
  width: 100%;
}

.block-title {
  margin: 14px 0 8px;
  font-weight: 600;
}

.output-block {
  margin: 0;
  padding: 12px;
  max-height: 260px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
}

.output-block.small {
  max-height: 220px;
}

.tips-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.tips-line {
  color: #4b5563;
  line-height: 1.8;
}
</style>
