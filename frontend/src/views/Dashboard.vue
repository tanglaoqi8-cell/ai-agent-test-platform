<template>
  <el-space direction="vertical" fill size="large" class="full-width">
    <el-card>
      <h2>通用 AI 测试评估平台</h2>
      <p>支持 Prompt、Agent、RAG 的统一测试对象管理、用例上传、测试执行和结果查看。</p>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card shadow="hover">
          <h3>测试对象</h3>
          <p>创建并管理 Prompt、Agent、RAG 测试对象。</p>
          <el-button type="primary" @click="$router.push('/test-targets')">进入</el-button>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <h3>用例管理</h3>
          <p>上传 CSV 并查看用例集和明细。</p>
          <el-button type="primary" @click="$router.push('/test-suites')">进入</el-button>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <h3>测试执行</h3>
          <p>选择测试对象和用例集后执行测试。</p>
          <el-button type="primary" @click="$router.push('/test-runs/create')">进入</el-button>
        </el-card>
      </el-col>
    </el-row>
  </el-space>
</template>

<style scoped>
.full-width {
  width: 100%;
}

h2,
h3 {
  margin: 0 0 10px;
}

p {
  margin: 0 0 12px;
  color: #4b5563;
}
</style>
