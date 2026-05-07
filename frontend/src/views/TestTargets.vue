<template>
  <el-space direction="vertical" fill size="large" class="full-width">
    <el-card>
      <template #header>
        <div class="card-header">新增测试对象</div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="名称"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12">
            <el-form-item label="测试对象类型">
              <el-select v-model="form.target_type" class="w-100">
                <el-option label="Prompt 测试" value="prompt" />
                <el-option label="Agent HTTP 接口" value="agent_http" />
                <el-option label="RAG HTTP 接口" value="rag_http" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述"><el-input v-model="form.description" /></el-form-item>
        <el-form-item label="接口地址"><el-input v-model="form.endpoint_url" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="请求方法"><el-input v-model="form.method" placeholder="例如：GET / POST" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="请求头 JSON"><el-input v-model="form.headers_json" placeholder='{"Authorization":"Bearer xxx"}' /></el-form-item></el-col>
        </el-row>
        <el-form-item label="请求体模板"><el-input v-model="form.body_template" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="Prompt 内容"><el-input v-model="form.prompt_content" type="textarea" :rows="4" /></el-form-item>

        <el-button type="primary" :loading="submitting" @click="handleCreate">新增</el-button>
      </el-form>
    </el-card>

    <el-card>
      <template #header>
        <div class="card-header">测试对象列表</div>
      </template>

      <el-table :data="targets" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="target_type" label="测试对象类型" width="140">
          <template #default="scope">
            <span>{{ renderTargetType(scope.row.target_type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="endpoint_url" label="接口地址" min-width="220" />
      </el-table>
    </el-card>
  </el-space>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { createTestTarget, getTestTargets } from "../api/testTargets";

const loading = ref(false);
const submitting = ref(false);
const targets = ref([]);

const form = reactive({
  name: "",
  target_type: "prompt",
  description: "",
  endpoint_url: "",
  method: "POST",
  headers_json: "",
  body_template: "",
  prompt_content: ""
});

async function fetchTargets() {
  loading.value = true;
  try {
    const { data } = await getTestTargets();
    targets.value = Array.isArray(data) ? data : data?.items || [];
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  if (!form.name) {
    ElMessage.warning("请填写名称");
    return;
  }

  submitting.value = true;
  try {
    await createTestTarget({ ...form });
    ElMessage.success("创建成功");
    await fetchTargets();
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    submitting.value = false;
  }
}

onMounted(fetchTargets);

function renderTargetType(type) {
  if (type === "prompt") return "Prompt 测试";
  if (type === "agent_http") return "Agent HTTP 接口";
  if (type === "rag_http") return "RAG HTTP 接口";
  return type || "-";
}
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
</style>
