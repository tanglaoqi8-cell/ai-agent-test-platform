<template>
  <el-container class="layout-root">
    <el-aside width="220px" class="layout-aside">
      <div class="logo">AI 测试平台</div>
      <el-menu
        :default-active="route.path"
        class="menu"
        router
      >
        <el-menu-item index="/">首页</el-menu-item>
        <el-menu-item index="/test-targets">测试对象</el-menu-item>
        <el-menu-item index="/test-suites">用例管理</el-menu-item>
        <el-menu-item index="/prompt-versions">Prompt 版本管理</el-menu-item>
        <el-menu-item index="/model-configs">模型配置管理</el-menu-item>
        <el-menu-item index="/prompt-run-once">Prompt 单轮执行</el-menu-item>
        <el-menu-item index="/test-runs/create">测试执行</el-menu-item>
        <el-menu-item index="/test-runs/results">执行结果</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="layout-header">通用 AI 测试评估平台</el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute } from "vue-router";

const route = useRoute();
</script>

<style scoped>
.layout-root {
  min-height: 100vh;
}

.layout-aside {
  border-right: 1px solid #e5e7eb;
  background: #fff;
}

.logo {
  height: 56px;
  line-height: 56px;
  text-align: center;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}

.menu {
  border-right: none;
}

.layout-header {
  border-bottom: 1px solid #e5e7eb;
  font-size: 18px;
  font-weight: 600;
  line-height: 60px;
}

.layout-main {
  background: #f7f8fa;
}
</style>
