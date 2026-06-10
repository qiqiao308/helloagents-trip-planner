<template>
  <div class="home-container">
    <div class="page-header">
      <h1 class="page-title">✈️ 智能旅行助手</h1>
      <p class="page-subtitle">基于 AI 的个性化旅行规划 —— 输入需求，秒出完整行程</p>
    </div>

    <a-card class="form-card" :bordered="false">
      <a-form
        :model="formData"
        layout="vertical"
        @finish="handleSubmit"
      >
        <!-- 目的地 & 天数 -->
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="目的地城市" name="city" :rules="[{ required: true, message: '请输入目的地' }]">
              <a-input
                v-model:value="formData.city"
                placeholder="如：北京、上海、杭州..."
                size="large"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="旅行天数" name="days">
              <a-input-number v-model:value="formData.days" :min="1" :max="14" size="large" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 开始日期 & 结束日期 -->
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="开始日期" name="start_date" :rules="[{ required: true }]">
              <a-date-picker v-model:value="startDate" size="large" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" name="end_date" :rules="[{ required: true }]">
              <a-date-picker v-model:value="endDate" size="large" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 偏好 & 预算 -->
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="旅行偏好" name="preferences">
              <a-select v-model:value="formData.preferences" size="large">
                <a-select-option value="历史文化">🏛️ 历史文化</a-select-option>
                <a-select-option value="自然风光">🏔️ 自然风光</a-select-option>
                <a-select-option value="美食探索">🍜 美食探索</a-select-option>
                <a-select-option value="休闲购物">🛍️ 休闲购物</a-select-option>
                <a-select-option value="亲子游乐">👨‍👩‍👧 亲子游乐</a-select-option>
                <a-select-option value="综合体验">🎯 综合体验</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="预算范围" name="budget">
              <a-select v-model:value="formData.budget" size="large">
                <a-select-option value="经济实惠">💡 经济实惠</a-select-option>
                <a-select-option value="中等">💰 中等</a-select-option>
                <a-select-option value="豪华旅行">👑 豪华旅行</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 交通 & 住宿 -->
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="交通方式" name="transportation">
              <a-select v-model:value="formData.transportation" size="large">
                <a-select-option value="公共交通">🚇 公共交通</a-select-option>
                <a-select-option value="自驾">🚗 自驾</a-select-option>
                <a-select-option value="出租车/网约车">🚕 出租车/网约车</a-select-option>
                <a-select-option value="租车+公共交通">🚗+🚇 混合</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="住宿类型" name="accommodation">
              <a-select v-model:value="formData.accommodation" size="large">
                <a-select-option value="经济型酒店">🏨 经济型酒店</a-select-option>
                <a-select-option value="舒适型酒店">🏩 舒适型酒店</a-select-option>
                <a-select-option value="豪华酒店">🏰 豪华酒店</a-select-option>
                <a-select-option value="民宿">🏡 民宿</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 提交按钮 -->
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            :loading="loading"
            block
          >
            {{ loading ? '正在规划中...' : '🚀 开始规划' }}
          </a-button>
        </a-form-item>

        <!-- 加载进度 -->
        <a-form-item v-if="loading">
          <a-progress :percent="loadingProgress" status="active" :format="percent => `${Math.round(percent)}%`" />
          <p class="loading-status">{{ loadingStatus }}</p>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 功能特色 -->
    <div class="features">
      <a-card title="✨ 核心功能" :bordered="false">
        <a-row :gutter="16">
          <a-col :span="6" v-for="f in features" :key="f.title">
            <a-statistic :title="f.title" :value="f.desc" />
          </a-col>
        </a-row>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { generateTripPlan } from '@/services/api'
import type { TripPlanRequest } from '@/types'

const router = useRouter()

const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

const startDate = ref<dayjs.Dayjs>()
const endDate = ref<dayjs.Dayjs>()

const formData = ref<Omit<TripPlanRequest, 'start_date' | 'end_date'> & { start_date?: string; end_date?: string }>({
  city: '',
  days: 3,
  preferences: '历史文化',
  budget: '中等',
  transportation: '公共交通',
  accommodation: '经济型酒店',
})

// 同步日期到 formData
watch(startDate, (val) => {
  formData.value.start_date = val?.format('YYYY-MM-DD') || ''
})
watch(endDate, (val) => {
  formData.value.end_date = val?.format('YYYY-MM-DD') || ''
})

const features = [
  { title: '🗺️', desc: '智能规划' },
  { title: '📍', desc: '地图可视化' },
  { title: '💰', desc: '预算明细' },
  { title: '📤', desc: '导出分享' },
]

const handleSubmit = async () => {
  if (!formData.value.city) {
    message.warning('请输入目的地城市')
    return
  }
  if (!formData.value.start_date || !formData.value.end_date) {
    message.warning('请选择旅行日期')
    return
  }

  loading.value = true
  loadingProgress.value = 0

  // 模拟进度更新
  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += Math.random() * 15 + 5
      if (loadingProgress.value <= 25) loadingStatus.value = '🔍 正在搜索景点信息...'
      else if (loadingProgress.value <= 45) loadingStatus.value = '🌤️ 正在查询天气...'
      else if (loadingProgress.value <= 65) loadingStatus.value = '🏨 正在推荐酒店...'
      else loadingStatus.value = '📋 正在生成行程计划...'
    }
  }, 600)

  try {
    const response = await generateTripPlan(formData.value as TripPlanRequest)
    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 规划完成！'
    setTimeout(() => {
      router.push({ name: 'result', state: { tripPlan: response } })
    }, 500)
  } catch (error: any) {
    clearInterval(progressInterval)
    message.error(error.message || '生成计划失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 36px;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  color: #8c8c8c;
  font-size: 16px;
}

.form-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
}

.loading-status {
  text-align: center;
  color: #1890ff;
  margin-top: 8px;
  font-size: 14px;
}

.features {
  margin-top: 24px;
}
</style>
