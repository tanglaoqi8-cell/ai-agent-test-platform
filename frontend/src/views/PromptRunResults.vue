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
          <div class="detail-actions">
            <el-button type="primary" @click="openScoreDialog">发起 LLM 自动评分</el-button>
            <el-button type="warning" @click="openManualReviewDialog">提交人工复核</el-button>
            <el-button type="success" @click="openSummaryDialog">查看摘要报告</el-button>
            <el-button type="info" @click="openMarkdownDialog">查看 Markdown 报告</el-button>
            <el-button type="primary" plain @click="openCompareDialog">Run 对比</el-button>
            <el-button @click="refreshDetail">刷新详情</el-button>
          </div>

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

    <el-dialog
      v-model="summaryDialogVisible"
      :title="`Prompt 摘要报告 - 执行批次ID ${detailRunId || '-'}`"
      width="70%"
    >
      <div v-loading="summaryLoading">
        <template v-if="summaryData">
          <div class="section-title">执行基本信息</div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="执行批次ID">{{ summaryBasicInfo.run_id }}</el-descriptions-item>
            <el-descriptions-item label="执行状态">{{ summaryBasicInfo.status }}</el-descriptions-item>
            <el-descriptions-item label="Prompt版本ID">{{ summaryBasicInfo.prompt_version_id }}</el-descriptions-item>
            <el-descriptions-item label="模型配置ID">{{ summaryBasicInfo.model_config_id }}</el-descriptions-item>
          </el-descriptions>

          <div class="section-title">结果统计</div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="总执行次数">{{ summaryStats.total }}</el-descriptions-item>
            <el-descriptions-item label="成功次数">{{ summaryStats.success_count }}</el-descriptions-item>
            <el-descriptions-item label="失败次数">{{ summaryStats.failed_count }}</el-descriptions-item>
            <el-descriptions-item label="成功率">{{ summaryStats.success_rate }}</el-descriptions-item>
            <el-descriptions-item label="断言通过次数">{{ summaryStats.assert_passed_count }}</el-descriptions-item>
            <el-descriptions-item label="断言失败次数">{{ summaryStats.assert_failed_count }}</el-descriptions-item>
            <el-descriptions-item label="断言跳过次数">{{ summaryStats.assert_skipped_count }}</el-descriptions-item>
            <el-descriptions-item label="断言通过率">{{ summaryStats.assert_pass_rate }}</el-descriptions-item>
          </el-descriptions>

          <div class="section-title">最新评分</div>
          <template v-if="summaryLatestScore">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="总分">{{ resolveField(summaryLatestScore, ["total_score", "score"]) }}</el-descriptions-item>
              <el-descriptions-item label="评分状态">{{ resolveField(summaryLatestScore, ["status"]) }}</el-descriptions-item>
              <el-descriptions-item label="评分理由" :span="2">
                {{ resolveField(summaryLatestScore, ["score_reason", "reason"]) }}
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty v-else description="暂无 LLM 自动评分" />

          <div class="section-title">最新人工复核</div>
          <template v-if="summaryLatestManualReview">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="人工判定">
                {{ resolveField(summaryLatestManualReview, ["manual_status", "status"]) }}
              </el-descriptions-item>
              <el-descriptions-item label="复核人">{{ resolveField(summaryLatestManualReview, ["reviewer"]) }}</el-descriptions-item>
              <el-descriptions-item label="人工备注" :span="2">
                {{ resolveField(summaryLatestManualReview, ["manual_remark", "remark"]) }}
              </el-descriptions-item>
              <el-descriptions-item label="复核时间">
                {{ formatDateTimeToChina(resolveField(summaryLatestManualReview, ["created_at", "updated_at"])) }}
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <el-empty v-else description="暂无人工复核记录" />

          <div class="section-title">人工确认建议</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="need_manual_check">{{ summaryManualCheck.need_manual_check }}</el-descriptions-item>
            <el-descriptions-item label="reasons">
              <pre class="long-block small">{{ summaryManualCheck.reasons }}</pre>
            </el-descriptions-item>
          </el-descriptions>

          <div class="section-title">失败摘要</div>
          <template v-if="summaryFailureList.length">
            <el-table :data="summaryFailureList" border>
              <el-table-column prop="case_id" label="用例ID" width="110" />
              <el-table-column prop="case_name" label="用例名称" min-width="180" />
              <el-table-column prop="reason" label="原因摘要" min-width="240" show-overflow-tooltip />
            </el-table>
          </template>
          <el-empty v-else description="暂无失败摘要" />
        </template>
      </div>
      <template #footer>
        <el-button type="primary" @click="summaryDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="markdownDialogVisible"
      :title="`Markdown 测试报告 - 执行批次ID ${detailRunId || '-'}`"
      width="75%"
    >
      <div v-loading="markdownLoading">
        <pre class="long-block markdown-block">{{ markdownContent }}</pre>
      </div>
      <template #footer>
        <el-button @click="copyMarkdown">复制 Markdown</el-button>
        <el-button type="primary" @click="markdownDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="compareDialogVisible"
      :title="`Run 对比 - 当前执行批次ID ${detailRunId || '-'}`"
      width="80%"
      @closed="resetCompareDialog"
    >
      <el-form ref="compareFormRef" :model="compareForm" :rules="compareFormRules" label-width="130px">
        <el-form-item label="基线执行批次ID" prop="baseline_run_id">
          <el-input
            v-model="compareForm.baseline_run_id"
            placeholder="请输入基线执行批次ID"
            clearable
          />
        </el-form-item>
      </el-form>

      <div class="compare-actions">
        <el-button type="primary" :loading="compareLoading" @click="submitCompare">开始对比</el-button>
      </div>

      <template v-if="compareResult">
        <div class="section-title">基本信息</div>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="当前执行批次ID">{{ compareBasicInfo.current_run_id }}</el-descriptions-item>
          <el-descriptions-item label="基线执行批次ID">{{ compareBasicInfo.baseline_run_id }}</el-descriptions-item>
          <el-descriptions-item label="基线关系">
            {{ compareBasicInfo.baseline_relation_matched }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">对比结论</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="结论">
            <el-tag>{{ compareConclusion }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">指标差异</div>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="成功率差异">{{ compareDiff.success_rate_diff }}</el-descriptions-item>
          <el-descriptions-item label="断言通过率差异">{{ compareDiff.assertion_pass_rate_diff }}</el-descriptions-item>
          <el-descriptions-item label="LLM总分差异">{{ compareDiff.total_score_diff }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">当前 Run 摘要</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行状态">{{ compareCurrentSummary.status }}</el-descriptions-item>
          <el-descriptions-item label="Prompt版本ID">{{ compareCurrentSummary.prompt_version_id }}</el-descriptions-item>
          <el-descriptions-item label="模型配置ID">{{ compareCurrentSummary.model_config_id }}</el-descriptions-item>
          <el-descriptions-item label="总执行次数">{{ compareCurrentSummary.total }}</el-descriptions-item>
          <el-descriptions-item label="成功次数">{{ compareCurrentSummary.success_count }}</el-descriptions-item>
          <el-descriptions-item label="失败次数">{{ compareCurrentSummary.failed_count }}</el-descriptions-item>
          <el-descriptions-item label="成功率">{{ compareCurrentSummary.success_rate }}</el-descriptions-item>
          <el-descriptions-item label="断言通过率">{{ compareCurrentSummary.assert_pass_rate }}</el-descriptions-item>
          <el-descriptions-item label="最新评分总分">{{ compareCurrentSummary.latest_score_total }}</el-descriptions-item>
          <el-descriptions-item label="最新人工复核">{{ compareCurrentSummary.latest_manual_review }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">基线 Run 摘要</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行状态">{{ compareBaselineSummary.status }}</el-descriptions-item>
          <el-descriptions-item label="Prompt版本ID">{{ compareBaselineSummary.prompt_version_id }}</el-descriptions-item>
          <el-descriptions-item label="模型配置ID">{{ compareBaselineSummary.model_config_id }}</el-descriptions-item>
          <el-descriptions-item label="总执行次数">{{ compareBaselineSummary.total }}</el-descriptions-item>
          <el-descriptions-item label="成功次数">{{ compareBaselineSummary.success_count }}</el-descriptions-item>
          <el-descriptions-item label="失败次数">{{ compareBaselineSummary.failed_count }}</el-descriptions-item>
          <el-descriptions-item label="成功率">{{ compareBaselineSummary.success_rate }}</el-descriptions-item>
          <el-descriptions-item label="断言通过率">{{ compareBaselineSummary.assert_pass_rate }}</el-descriptions-item>
          <el-descriptions-item label="最新评分总分">{{ compareBaselineSummary.latest_score_total }}</el-descriptions-item>
          <el-descriptions-item label="最新人工复核">{{ compareBaselineSummary.latest_manual_review }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">对比原因</div>
        <pre class="long-block small">{{ compareReasonsText }}</pre>

        <div class="section-title">人工确认建议</div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="是否建议人工确认">{{ compareManualSuggestion.need_manual_check }}</el-descriptions-item>
          <el-descriptions-item label="原因">
            <pre class="long-block small">{{ compareManualSuggestion.reasons }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <template #footer>
        <el-button @click="compareDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="scoreDialogVisible" title="发起 LLM 自动评分" width="640px" @closed="resetScoreDialog">
      <el-form ref="scoreFormRef" :model="scoreForm" :rules="scoreFormRules" label-width="130px">
        <el-form-item label="评分模型配置" prop="scorer_model_config_id">
          <el-select
            v-model="scoreForm.scorer_model_config_id"
            class="w-100"
            placeholder="请选择评分模型配置"
            :loading="scorerOptionsLoading"
          >
            <el-option
              v-for="item in scorerModelConfigs"
              :key="item.id"
              :label="`${item.id} - ${item.config_name || '-'} - ${item.model || '-'}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="预期行为">
          <el-input
            v-model="scoreForm.expected_behavior"
            type="textarea"
            :rows="4"
            placeholder="输出应围绕用户输入进行回答，并满足断言或业务预期。"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="scoreForm.remark" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scoreDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="scoreSubmitting" @click="submitScore">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="manualReviewDialogVisible" title="提交人工复核" width="640px" @closed="resetManualReviewDialog">
      <el-form ref="manualReviewFormRef" :model="manualReviewForm" :rules="manualReviewRules" label-width="120px">
        <el-form-item label="人工判定" prop="manual_status">
          <el-select v-model="manualReviewForm.manual_status" class="w-100" placeholder="请选择人工判定">
            <el-option label="通过" value="passed" />
            <el-option label="失败" value="failed" />
            <el-option label="待确认" value="pending" />
          </el-select>
        </el-form-item>
        <el-form-item label="人工备注">
          <el-input v-model="manualReviewForm.manual_remark" type="textarea" :rows="4" placeholder="可选" />
        </el-form-item>
        <el-form-item label="复核人">
          <el-input v-model="manualReviewForm.reviewer" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manualReviewDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="manualReviewSubmitting" @click="submitManualReview">提交</el-button>
      </template>
    </el-dialog>
  </el-space>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { getModelConfigs } from "../api/modelConfigs";
import {
  comparePromptTestRuns,
  createPromptManualReview,
  getPromptTestRunMarkdownReport,
  getPromptTestRunDetail,
  getPromptTestRuns,
  getPromptTestRunSummary,
  scorePromptTestRun
} from "../api/promptTestRuns";
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
const scoreDialogVisible = ref(false);
const scoreSubmitting = ref(false);
const scorerOptionsLoading = ref(false);
const scorerModelConfigs = ref([]);
const scoreFormRef = ref(null);
const manualReviewDialogVisible = ref(false);
const manualReviewSubmitting = ref(false);
const manualReviewFormRef = ref(null);
const summaryDialogVisible = ref(false);
const summaryLoading = ref(false);
const summaryData = ref(null);
const markdownDialogVisible = ref(false);
const markdownLoading = ref(false);
const markdownContent = ref("-");
const compareDialogVisible = ref(false);
const compareLoading = ref(false);
const compareResult = ref(null);
const compareFormRef = ref(null);

const scoreForm = reactive({
  scorer_model_config_id: null,
  expected_behavior: "",
  remark: ""
});

const scoreFormRules = {
  scorer_model_config_id: [{ required: true, message: "请选择评分模型配置", trigger: "change" }]
};

const manualReviewForm = reactive({
  manual_status: "",
  manual_remark: "",
  reviewer: ""
});

const manualReviewRules = {
  manual_status: [{ required: true, message: "请选择人工判定", trigger: "change" }]
};
const compareForm = reactive({
  baseline_run_id: ""
});
const compareFormRules = {
  baseline_run_id: [
    { required: true, message: "请输入基线执行批次ID", trigger: "blur" },
    {
      validator: (_, value, callback) => {
        if (!/^\d+$/.test(String(value || "").trim())) {
          callback(new Error("基线执行批次ID必须是数字"));
          return;
        }
        if (String(value).trim() === String(detailRunId.value)) {
          callback(new Error("基线执行批次ID不能与当前执行批次ID相同"));
          return;
        }
        callback();
      },
      trigger: "blur"
    }
  ]
};

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
const summaryBasicInfo = computed(() => normalizeRunBasicInfo(summaryData.value));
const summaryStats = computed(() => normalizeSummaryStats(summaryData.value));
const summaryLatestScore = computed(() => summaryData.value?.latest_score || summaryData.value?.score || null);
const summaryLatestManualReview = computed(() => summaryData.value?.latest_manual_review || summaryData.value?.manual_review || null);
const summaryManualCheck = computed(() => normalizeSummaryManualCheck(summaryData.value));
const summaryFailureList = computed(() => normalizeSummaryFailureList(summaryData.value));
const compareBasicInfo = computed(() => {
  const d = compareResult.value || {};
  return {
    current_run_id: d.current_run_id ?? detailRunId.value ?? "-",
    baseline_run_id: d.baseline_run_id ?? compareForm.baseline_run_id ?? "-",
    baseline_relation_matched: formatBaselineRelationMatched(d.baseline_relation_matched)
  };
});
const compareConclusion = computed(() => {
  const result = compareResult.value?.comparison?.result;
  const map = {
    better: "当前更好",
    worse: "当前更差",
    equal: "基本一致",
    need_manual_check: "需要人工确认"
  };
  return map[result] || "-";
});
const compareDiff = computed(() => {
  const c = compareResult.value?.comparison || {};
  return {
    success_rate_diff: formatRateDiff(c.success_rate_diff),
    assertion_pass_rate_diff: formatRateDiff(c.assertion_pass_rate_diff),
    total_score_diff: formatScoreDiff(c.total_score_diff)
  };
});
const compareCurrentSummary = computed(() => normalizeCompareSummary(compareResult.value?.current_summary));
const compareBaselineSummary = computed(() => normalizeCompareSummary(compareResult.value?.baseline_summary));
const compareManualSuggestion = computed(() => normalizeCompareManualSuggestion(compareResult.value?.manual_check_suggestion));
const compareReasonsText = computed(() => normalizeCompareReasons(compareResult.value?.comparison?.reasons));

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

function normalizeSummaryStats(data) {
  const d = data || {};
  const stat = d.summary || d.stats || d.statistics || d;
  return {
    total: stat.total ?? stat.total_count ?? stat.run_total ?? "-",
    success_count: stat.success_count ?? stat.success ?? stat.passed_count ?? "-",
    failed_count: stat.failed_count ?? stat.failed ?? "-",
    success_rate: stat.success_rate ?? stat.pass_rate ?? "-",
    assert_passed_count: stat.assert_passed_count ?? stat.assertion_passed_count ?? "-",
    assert_failed_count: stat.assert_failed_count ?? stat.assertion_failed_count ?? "-",
    assert_skipped_count: stat.assert_skipped_count ?? stat.assertion_skipped_count ?? "-",
    assert_pass_rate: stat.assert_pass_rate ?? stat.assertion_pass_rate ?? "-"
  };
}

function normalizeSummaryManualCheck(data) {
  const d = data || {};
  const manual = d.manual_check || d.manual_advice || {};
  const reasons = manual.reasons ?? d.reasons ?? [];
  return {
    need_manual_check: manual.need_manual_check ?? d.need_manual_check ?? "-",
    reasons: Array.isArray(reasons) ? (reasons.length ? reasons.join("\n") : "-") : formatMaybeJson(reasons)
  };
}

function normalizeSummaryFailureList(data) {
  const list = data?.failure_summary || data?.failures || [];
  if (!Array.isArray(list)) return [];
  return list.slice(0, 5).map((item, index) => ({
    case_id: item?.case_id ?? item?.id ?? index + 1,
    case_name: item?.case_name ?? item?.name ?? "-",
    reason: summarizeOutput(item?.reason ?? item?.message ?? item?.error_message ?? "-")
  }));
}

function formatBaselineRelationMatched(value) {
  if (value === true) return "基线关系匹配";
  if (value === false) return "基线关系不匹配";
  return "未配置基线关系";
}

function formatRateDiff(value) {
  if (value === null || value === undefined || value === "") return "-";
  const num = Number(value);
  if (!Number.isFinite(num)) return String(value);
  const pct = (num * 100).toFixed(2);
  return `${num > 0 ? "+" : ""}${pct}%`;
}

function formatScoreDiff(value) {
  if (value === null || value === undefined || value === "") return "-";
  const num = Number(value);
  if (!Number.isFinite(num)) return String(value);
  if (num > 0) return `+${num}`;
  return String(num);
}

function normalizeCompareSummary(summary) {
  const s = summary || {};
  return {
    status: resolveField(s, ["status", "run_status"]),
    prompt_version_id: resolveField(s, ["prompt_version_id"]),
    model_config_id: resolveField(s, ["model_config_id"]),
    total: resolveField(s, ["total", "total_count"]),
    success_count: resolveField(s, ["success_count", "success"]),
    failed_count: resolveField(s, ["failed_count", "failed"]),
    success_rate: resolveField(s, ["success_rate", "pass_rate"]),
    assert_pass_rate: resolveField(s, ["assert_pass_rate", "assertion_pass_rate"]),
    latest_score_total:
      resolveField(s?.latest_score || {}, ["total_score", "score"]) !== "-"
        ? resolveField(s?.latest_score || {}, ["total_score", "score"])
        : "-",
    latest_manual_review:
      resolveField(s?.latest_manual_review || {}, ["manual_status", "status"]) !== "-"
        ? resolveField(s?.latest_manual_review || {}, ["manual_status", "status"])
        : "-"
  };
}

function normalizeCompareReasons(reasons) {
  if (Array.isArray(reasons)) {
    return reasons.length ? reasons.join("\n") : "暂无对比原因";
  }
  if (reasons && String(reasons).trim()) return String(reasons);
  return "暂无对比原因";
}

function normalizeCompareManualSuggestion(data) {
  const s = data || {};
  const rawNeed = s.need_manual_check;
  let needManual = "-";
  if (rawNeed === true) needManual = "是";
  else if (rawNeed === false) needManual = "否";
  const reasons = Array.isArray(s.reasons) ? (s.reasons.length ? s.reasons.join("\n") : "暂无") : s.reasons || "暂无";
  return {
    need_manual_check: needManual,
    reasons
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

async function refreshDetail(showSuccess = false) {
  if (!detailRunId.value) return;
  await refreshDetailByRunId(detailRunId.value, showSuccess);
}

async function refreshDetailByRunId(runId, showSuccess = false) {
  if (!runId) return false;
  detailLoading.value = true;
  try {
    const { data } = await getPromptTestRunDetail(runId);
    detailData.value = data;
    if (showSuccess) ElMessage.success("详情已刷新");
    return true;
  } catch (error) {
    ElMessage.error(error.message || "刷新详情失败");
    return false;
  } finally {
    detailLoading.value = false;
  }
}

async function loadScorerModelConfigs() {
  if (scorerModelConfigs.value.length > 0) return;
  scorerOptionsLoading.value = true;
  try {
    const { data } = await getModelConfigs({ status: "active" });
    const list = Array.isArray(data) ? data : data?.items || [];
    scorerModelConfigs.value = list.filter((item) => item?.status === "active");
  } catch (error) {
    ElMessage.error(error.message || "加载模型配置失败");
  } finally {
    scorerOptionsLoading.value = false;
  }
}

async function openScoreDialog() {
  await loadScorerModelConfigs();
  scoreDialogVisible.value = true;
}

function resetScoreDialog() {
  scoreForm.scorer_model_config_id = null;
  scoreForm.expected_behavior = "";
  scoreForm.remark = "";
  scoreSubmitting.value = false;
  scoreFormRef.value?.clearValidate();
}

async function submitScore() {
  if (!detailRunId.value || !scoreFormRef.value) return;
  const valid = await scoreFormRef.value.validate().catch(() => false);
  if (!valid) return;

  const runId = detailRunId.value;
  scoreSubmitting.value = true;
  try {
    await scorePromptTestRun(runId, {
      scorer_model_config_id: scoreForm.scorer_model_config_id,
      expected_behavior: scoreForm.expected_behavior || "",
      remark: scoreForm.remark || ""
    });
    ElMessage.success("评分完成");
    resetScoreDialog();
    scoreDialogVisible.value = false;
    await nextTick();
    let refreshed = await refreshDetailByRunId(runId, false);
    if (!refreshed || !detailData.value?.latest_score) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      await refreshDetailByRunId(runId, false);
    }
  } catch (error) {
    const message = error.message || "评分失败";
    if (String(message).toLowerCase().includes("timeout")) {
      ElMessage.error("LLM 评分时间较长，请稍后重试或检查后端/模型服务状态。");
    } else {
      ElMessage.error(message);
    }
  } finally {
    scoreSubmitting.value = false;
  }
}

function openManualReviewDialog() {
  manualReviewDialogVisible.value = true;
}

function resetManualReviewDialog() {
  manualReviewForm.manual_status = "";
  manualReviewForm.manual_remark = "";
  manualReviewForm.reviewer = "";
  manualReviewSubmitting.value = false;
  manualReviewFormRef.value?.clearValidate();
}

async function submitManualReview() {
  if (!detailRunId.value || !manualReviewFormRef.value) return;
  const valid = await manualReviewFormRef.value.validate().catch(() => false);
  if (!valid) return;

  manualReviewSubmitting.value = true;
  try {
    await createPromptManualReview(detailRunId.value, {
      manual_status: manualReviewForm.manual_status,
      manual_remark: manualReviewForm.manual_remark || "",
      reviewer: manualReviewForm.reviewer || ""
    });
    ElMessage.success("人工复核已提交");
    manualReviewDialogVisible.value = false;
    await refreshDetail(false);
  } catch (error) {
    ElMessage.error(error.message || "人工复核提交失败");
  } finally {
    manualReviewSubmitting.value = false;
  }
}

async function openSummaryDialog() {
  if (!detailRunId.value) return;
  summaryDialogVisible.value = true;
  summaryLoading.value = true;
  summaryData.value = null;
  try {
    const { data } = await getPromptTestRunSummary(detailRunId.value);
    summaryData.value = data || {};
  } catch (error) {
    ElMessage.error(error.message || "获取摘要报告失败");
  } finally {
    summaryLoading.value = false;
  }
}

async function openMarkdownDialog() {
  if (!detailRunId.value) return;
  markdownDialogVisible.value = true;
  markdownLoading.value = true;
  markdownContent.value = "-";
  try {
    const { data } = await getPromptTestRunMarkdownReport(detailRunId.value);
    markdownContent.value = data ? String(data) : "-";
  } catch (error) {
    ElMessage.error(error.message || "获取 Markdown 报告失败");
  } finally {
    markdownLoading.value = false;
  }
}

async function copyMarkdown() {
  const text = markdownContent.value || "";
  if (!text || text === "-") return;
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    ElMessage.success("已复制");
  } catch {
    ElMessage.error("复制失败，请手动复制");
  }
}

function openCompareDialog() {
  compareDialogVisible.value = true;
}

function resetCompareDialog() {
  compareForm.baseline_run_id = "";
  compareFormRef.value?.clearValidate();
  compareLoading.value = false;
  compareResult.value = null;
}

async function submitCompare() {
  if (!detailRunId.value || !compareFormRef.value) return;
  const valid = await compareFormRef.value.validate().catch(() => false);
  if (!valid) return;
  compareLoading.value = true;
  try {
    const { data } = await comparePromptTestRuns(detailRunId.value, Number(compareForm.baseline_run_id));
    compareResult.value = data || {};
  } catch (error) {
    const status = error?.response?.status;
    if (status === 400) {
      ElMessage.error("对比参数无效，请检查基线执行批次ID。");
    } else if (status === 404) {
      ElMessage.error("基线执行批次不存在，请确认后重试。");
    } else {
      ElMessage.error(error.message || "Run 对比失败");
    }
  } finally {
    compareLoading.value = false;
  }
}

function closeDetail() {
  detailData.value = null;
  detailRunId.value = null;
  detailLoading.value = false;
  scoreDialogVisible.value = false;
  manualReviewDialogVisible.value = false;
  summaryDialogVisible.value = false;
  markdownDialogVisible.value = false;
  compareDialogVisible.value = false;
  summaryData.value = null;
  markdownContent.value = "-";
  compareResult.value = null;
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

.detail-actions {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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

.w-100 {
  width: 100%;
}

.markdown-block {
  max-height: 60vh;
}

.compare-actions {
  margin-bottom: 12px;
}
</style>
