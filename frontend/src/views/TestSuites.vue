<template>
  <el-space direction="vertical" fill size="large" class="full-width">
    <el-card>
      <template #header><div class="card-header">上传 CSV 用例</div></template>
      <el-form :model="uploadForm" label-width="120px">
        <el-form-item label="用例集名称">
          <el-input v-model="uploadForm.suite_name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" />
        </el-form-item>
        <el-form-item label="CSV 文件">
          <input type="file" accept=".csv" @change="onFileChange" />
        </el-form-item>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </el-form>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card>
          <template #header><div class="card-header">用例集列表</div></template>
          <el-table :data="suites" border v-loading="loadingSuites" @row-click="handleSuiteClick">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="suite_name" label="用例集名称" min-width="160" />
            <el-table-column prop="description" label="描述" min-width="180" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">用例详情 {{ currentSuite ? `(用例集ID: ${currentSuite.id})` : "" }}</div>
          </template>
          <el-table :data="cases" border v-loading="loadingCases">
            <el-table-column prop="id" label="用例ID" width="80" />
            <el-table-column prop="case_name" label="用例名称" min-width="160" />
            <el-table-column prop="input_text" label="输入内容" min-width="200" />
            <el-table-column prop="expected_value" label="期望值" min-width="180" />
            <el-table-column prop="assert_type" label="断言类型" width="120" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </el-space>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { getSuiteCases, getTestSuites, uploadTestCases } from "../api/testCases";

const uploadForm = reactive({
  suite_name: "",
  description: ""
});
const selectedFile = ref(null);
const uploading = ref(false);

const suites = ref([]);
const cases = ref([]);
const currentSuite = ref(null);
const loadingSuites = ref(false);
const loadingCases = ref(false);

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null;
}

async function fetchSuites() {
  loadingSuites.value = true;
  try {
    const { data } = await getTestSuites();
    suites.value = Array.isArray(data) ? data : data?.items || [];
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loadingSuites.value = false;
  }
}

async function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning("请选择 CSV 文件");
    return;
  }
  if (!uploadForm.suite_name) {
    ElMessage.warning("请填写用例集名称");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile.value);
  formData.append("suite_name", uploadForm.suite_name);
  formData.append("description", uploadForm.description || "");

  uploading.value = true;
  try {
    await uploadTestCases(formData);
    ElMessage.success("上传成功");
    await fetchSuites();
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    uploading.value = false;
  }
}

async function handleSuiteClick(row) {
  currentSuite.value = row;
  loadingCases.value = true;
  try {
    const { data } = await getSuiteCases(row.id);
    cases.value = Array.isArray(data) ? data : data?.items || [];
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loadingCases.value = false;
  }
}

onMounted(fetchSuites);
</script>

<style scoped>
.full-width {
  width: 100%;
}

.card-header {
  font-weight: 600;
}
</style>
