<template>
  <el-space direction="vertical" fill size="large" class="full-width">
    <el-card>
      <template #header>
        <div class="header-row">
          <span class="page-title">模型配置管理</span>
          <div class="actions">
            <el-button type="primary" @click="openCreateDialog">新增模型配置</el-button>
            <el-button @click="fetchList">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" border v-loading="listLoading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="config_name" label="配置名称" min-width="140" />
        <el-table-column prop="provider" label="Provider" width="120" />
        <el-table-column prop="base_url" label="Base URL" min-width="180" show-overflow-tooltip />
        <el-table-column prop="model" label="模型名称" min-width="130" show-overflow-tooltip />
        <el-table-column prop="temperature" label="Temperature" width="110" />
        <el-table-column prop="top_p" label="Top P" width="90" />
        <el-table-column prop="max_tokens" label="Max Tokens" width="120" />
        <el-table-column label="是否默认" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_default ? 'success' : 'info'">{{ scope.row.is_default ? "是" : "否" }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" min-width="160" />
        <el-table-column prop="updated_at" label="更新时间" min-width="160" />
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="openViewDialog(scope.row.id)">查看</el-button>
            <el-button link type="primary" @click="openEditDialog(scope.row.id)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="formDialogVisible" :title="isEditMode ? '编辑模型配置' : '新增模型配置'" width="760px" @closed="resetFormDialog">
      <el-form ref="formRef" :model="formModel" :rules="formRules" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="配置名称" prop="config_name">
              <el-input v-model="formModel.config_name" placeholder="请输入配置名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Provider" prop="provider">
              <el-input v-model="formModel.provider" placeholder="afh_proxy" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="formModel.base_url" placeholder="https://afh-key.sz-index.com/v1" />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="模型名称" prop="model">
              <el-input v-model="formModel.model" placeholder="qwen3.5-plus" />
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

        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="Temperature" prop="temperature">
              <el-input-number v-model="formModel.temperature" class="w-100" :precision="2" :step="0.1" controls-position="right" placeholder="0.7" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Top P" prop="top_p">
              <el-input-number v-model="formModel.top_p" class="w-100" :precision="2" :step="0.1" controls-position="right" placeholder="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Max Tokens" prop="max_tokens">
              <el-input-number v-model="formModel.max_tokens" class="w-100" :min="1" :step="1" :precision="0" controls-position="right" placeholder="2048" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="是否默认">
              <el-switch v-model="formModel.is_default" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备注">
              <el-input v-model="formModel.remark" placeholder="可选" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">{{ isEditMode ? "保存" : "创建" }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDialogVisible" title="模型配置详情" width="760px" @closed="viewDetail = null">
      <el-descriptions v-if="viewDetail" :column="2" border>
        <el-descriptions-item label="ID">{{ viewDetail.id }}</el-descriptions-item>
        <el-descriptions-item label="配置名称">{{ viewDetail.config_name }}</el-descriptions-item>
        <el-descriptions-item label="Provider">{{ viewDetail.provider }}</el-descriptions-item>
        <el-descriptions-item label="Base URL">{{ viewDetail.base_url }}</el-descriptions-item>
        <el-descriptions-item label="模型名称">{{ viewDetail.model }}</el-descriptions-item>
        <el-descriptions-item label="Temperature">{{ viewDetail.temperature }}</el-descriptions-item>
        <el-descriptions-item label="Top P">{{ viewDetail.top_p }}</el-descriptions-item>
        <el-descriptions-item label="Max Tokens">{{ viewDetail.max_tokens }}</el-descriptions-item>
        <el-descriptions-item label="是否默认">{{ viewDetail.is_default ? "是" : "否" }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ viewDetail.status }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ viewDetail.remark || "-" }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ viewDetail.created_at || "-" }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ viewDetail.updated_at || "-" }}</el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button type="primary" @click="viewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </el-space>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { createModelConfig, getModelConfigDetail, getModelConfigs, updateModelConfig } from "../api/modelConfigs";

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
  config_name: "",
  provider: "",
  base_url: "",
  model: "",
  temperature: null,
  top_p: null,
  max_tokens: null,
  is_default: false,
  status: "active",
  remark: ""
});

const formModel = reactive(createInitialForm());

const formRules = {
  config_name: [{ required: true, message: "请输入配置名称", trigger: "blur" }],
  provider: [{ required: true, message: "请输入 Provider", trigger: "blur" }],
  base_url: [{ required: true, message: "请输入 Base URL", trigger: "blur" }],
  model: [{ required: true, message: "请输入模型名称", trigger: "blur" }],
  temperature: [{ required: true, message: "请输入 Temperature", trigger: "change" }],
  top_p: [{ required: true, message: "请输入 Top P", trigger: "change" }],
  max_tokens: [{ required: true, message: "请输入 Max Tokens", trigger: "change" }]
};

function normalizeListResponse(data) {
  return Array.isArray(data) ? data : data?.items || [];
}

function normalizeDetailToForm(detail) {
  return {
    config_name: detail?.config_name || "",
    provider: detail?.provider || "",
    base_url: detail?.base_url || "",
    model: detail?.model || "",
    temperature: detail?.temperature ?? null,
    top_p: detail?.top_p ?? null,
    max_tokens: detail?.max_tokens ?? null,
    is_default: Boolean(detail?.is_default),
    status: detail?.status || "active",
    remark: detail?.remark || ""
  };
}

function buildPayloadFromForm() {
  return {
    config_name: formModel.config_name,
    provider: formModel.provider,
    base_url: formModel.base_url,
    model: formModel.model,
    temperature: formModel.temperature,
    top_p: formModel.top_p,
    max_tokens: formModel.max_tokens,
    is_default: Boolean(formModel.is_default),
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
    const { data } = await getModelConfigs();
    list.value = normalizeListResponse(data);
  } catch (error) {
    ElMessage.error(error.message || "获取模型配置列表失败");
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
    const { data } = await getModelConfigDetail(id);
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
    const { data } = await getModelConfigDetail(id);
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
      await updateModelConfig(editingId.value, payload);
      ElMessage.success("更新成功");
    } else {
      await createModelConfig(payload);
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
</style>
