<template>
  <el-space direction="vertical" fill size="large" class="full-width">
    <el-card>
      <template #header>
        <div class="header-row">
          <span class="page-title">Prompt 版本管理</span>
          <div class="actions">
            <el-button type="primary" @click="openCreateDialog">新增 Prompt 版本</el-button>
            <el-button @click="fetchList">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" border v-loading="listLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="prompt_name" label="Prompt 名称" min-width="150" />
        <el-table-column prop="version" label="版本号" width="120" />
        <el-table-column label="是否基线版本" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.is_baseline ? 'success' : 'info'">{{ scope.row.is_baseline ? "是" : "否" }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="baseline_version_id" label="基线版本ID" width="120" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" min-width="170" />
        <el-table-column prop="updated_at" label="更新时间" min-width="170" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openViewDialog(scope.row.id)">查看</el-button>
            <el-button link type="primary" @click="openEditDialog(scope.row.id)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="formDialogVisible" :title="isEditMode ? '编辑 Prompt 版本' : '新增 Prompt 版本'" width="760px" @closed="resetFormDialog">
      <el-form ref="formRef" :model="formModel" :rules="formRules" label-width="120px">
        <el-form-item label="Prompt 名称" prop="prompt_name">
          <el-input v-model="formModel.prompt_name" placeholder="请输入 Prompt 名称" />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="版本号" prop="version">
              <el-input v-model="formModel.version" placeholder="请输入版本号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="formModel.status" class="w-100" placeholder="请选择状态">
                <el-option label="active" value="active" />
                <el-option label="inactive" value="inactive" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="Prompt 内容" prop="prompt_content">
          <el-input v-model="formModel.prompt_content" type="textarea" :rows="8" placeholder="请输入 Prompt 内容" />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="是否基线版本">
              <el-switch v-model="formModel.is_baseline" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="基线版本ID">
              <el-input-number v-model="formModel.baseline_version_id" class="w-100" :min="1" :step="1" controls-position="right" placeholder="可为空" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注">
          <el-input v-model="formModel.remark" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">{{ isEditMode ? "保存" : "创建" }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDialogVisible" title="Prompt 版本详情" width="760px" @closed="viewDetail = null">
      <el-descriptions v-if="viewDetail" :column="2" border>
        <el-descriptions-item label="ID">{{ viewDetail.id }}</el-descriptions-item>
        <el-descriptions-item label="Prompt 名称">{{ viewDetail.prompt_name }}</el-descriptions-item>
        <el-descriptions-item label="版本号">{{ viewDetail.version }}</el-descriptions-item>
        <el-descriptions-item label="是否基线版本">{{ viewDetail.is_baseline ? "是" : "否" }}</el-descriptions-item>
        <el-descriptions-item label="基线版本ID">{{ viewDetail.baseline_version_id ?? "-" }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ viewDetail.status }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ viewDetail.remark || "-" }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ viewDetail.created_at || "-" }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ viewDetail.updated_at || "-" }}</el-descriptions-item>
      </el-descriptions>

      <div class="content-title">Prompt 内容</div>
      <pre class="prompt-content">{{ viewDetail?.prompt_content || "" }}</pre>

      <template #footer>
        <el-button type="primary" @click="viewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </el-space>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { createPromptVersion, getPromptVersionDetail, getPromptVersions, updatePromptVersion } from "../api/promptVersions";

const listLoading = ref(false);
const list = ref([]);

const formDialogVisible = ref(false);
const viewDialogVisible = ref(false);
const submitLoading = ref(false);
const isEditMode = ref(false);
const editingId = ref(null);
const formRef = ref(null);
const viewDetail = ref(null);

const createInitialForm = () => ({
  prompt_name: "",
  version: "",
  prompt_content: "",
  is_baseline: false,
  baseline_version_id: null,
  status: "active",
  remark: ""
});

const formModel = reactive(createInitialForm());

const formRules = {
  prompt_name: [{ required: true, message: "请输入 Prompt 名称", trigger: "blur" }],
  version: [{ required: true, message: "请输入版本号", trigger: "blur" }],
  prompt_content: [{ required: true, message: "请输入 Prompt 内容", trigger: "blur" }]
};

function normalizeListResponse(data) {
  return Array.isArray(data) ? data : data?.items || [];
}

function normalizeDetailToForm(detail) {
  return {
    prompt_name: detail?.prompt_name || "",
    version: detail?.version || "",
    prompt_content: detail?.prompt_content || "",
    is_baseline: Boolean(detail?.is_baseline),
    baseline_version_id: detail?.baseline_version_id ?? null,
    status: detail?.status || "active",
    remark: detail?.remark || ""
  };
}

function buildPayloadFromForm() {
  return {
    prompt_name: formModel.prompt_name,
    version: formModel.version,
    prompt_content: formModel.prompt_content,
    is_baseline: Boolean(formModel.is_baseline),
    baseline_version_id: formModel.baseline_version_id ?? null,
    status: formModel.status,
    remark: formModel.remark || ""
  };
}

function fillForm(data) {
  Object.assign(formModel, createInitialForm(), data || {});
}

function resetFormDialog() {
  isEditMode.value = false;
  editingId.value = null;
  submitLoading.value = false;
  fillForm(createInitialForm());
  formRef.value?.clearValidate();
}

async function fetchList() {
  listLoading.value = true;
  try {
    const { data } = await getPromptVersions();
    list.value = normalizeListResponse(data);
  } catch (error) {
    ElMessage.error(error.message || "获取 Prompt 版本列表失败");
  } finally {
    listLoading.value = false;
  }
}

function openCreateDialog() {
  isEditMode.value = false;
  editingId.value = null;
  fillForm(createInitialForm());
  formDialogVisible.value = true;
}

async function openEditDialog(id) {
  isEditMode.value = true;
  editingId.value = id;
  formDialogVisible.value = true;
  try {
    const { data } = await getPromptVersionDetail(id);
    fillForm(normalizeDetailToForm(data));
  } catch (error) {
    ElMessage.error(error.message || "获取详情失败");
    formDialogVisible.value = false;
  }
}

async function openViewDialog(id) {
  viewDialogVisible.value = true;
  viewDetail.value = null;
  try {
    const { data } = await getPromptVersionDetail(id);
    viewDetail.value = data;
  } catch (error) {
    ElMessage.error(error.message || "获取详情失败");
    viewDialogVisible.value = false;
  }
}

async function submitForm() {
  if (!formRef.value) return;

  const valid = await formRef.value.validate().catch(() => false);
  if (!valid) return;

  submitLoading.value = true;
  try {
    const payload = buildPayloadFromForm();
    if (isEditMode.value && editingId.value) {
      await updatePromptVersion(editingId.value, payload);
      ElMessage.success("更新成功");
    } else {
      await createPromptVersion(payload);
      ElMessage.success("创建成功");
    }

    formDialogVisible.value = false;
    await fetchList();
  } catch (error) {
    ElMessage.error(error.message || "提交失败");
  } finally {
    submitLoading.value = false;
  }
}

onMounted(fetchList);
</script>

<style scoped>
.full-width {
  width: 100%;
}

.page-title {
  font-weight: 600;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.actions {
  display: flex;
  gap: 8px;
}

.w-100 {
  width: 100%;
}

.content-title {
  margin: 14px 0 8px;
  font-weight: 600;
}

.prompt-content {
  margin: 0;
  padding: 12px;
  max-height: 360px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
}
</style>
