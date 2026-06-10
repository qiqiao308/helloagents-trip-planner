<template>
  <div class="result-container">
    <!-- 侧边导航 -->
    <a-affix :offset-top="80" class="side-nav">
      <a-menu
        :selectedKeys="[activeSection]"
        mode="inline"
        @click="scrollToSection"
      >
        <a-menu-item key="overview">📋 行程概览</a-menu-item>
        <a-menu-item key="budget" v-if="tripPlan.budget">💰 预算明细</a-menu-item>
        <a-menu-item key="map">🗺️ 景点地图</a-menu-item>
        <a-menu-item key="days">📅 每日行程</a-menu-item>
        <a-menu-item key="weather" v-if="tripPlan.weather_info?.length">🌤️ 天气信息</a-menu-item>
        <a-menu-item key="suggestions">💡 旅行建议</a-menu-item>
      </a-menu>
    </a-affix>

    <!-- 主内容区 -->
    <div class="main-content" id="trip-plan-content">
      <!-- 标题栏 -->
      <div class="header-bar">
        <a-button @click="$router.push('/')" type="text">
          ← 返回首页
        </a-button>
        <h2>📍 {{ tripPlan.city }} · {{ tripPlan.days.length }} 天旅行计划</h2>
        <div class="header-actions">
          <a-button @click="toggleEditMode" :type="editMode ? 'primary' : 'default'">
            {{ editMode ? '完成编辑' : '✏️ 编辑行程' }}
          </a-button>
          <a-dropdown>
            <a-button>📥 导出行程</a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item @click="exportAsImage">导出为图片 (.png)</a-menu-item>
                <a-menu-item @click="exportAsPDF">导出为 PDF</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>

      <!-- 概览 -->
      <a-card id="overview" title="📋 行程概览" class="section-card" :bordered="false">
        <a-descriptions bordered size="small" :column="2">
          <a-descriptions-item label="目的地">{{ tripPlan.city }}</a-descriptions-item>
          <a-descriptions-item label="日期">{{ tripPlan.start_date }} → {{ tripPlan.end_date }}</a-descriptions-item>
          <a-descriptions-item label="天数">{{ tripPlan.days.length }} 天</a-descriptions-item>
          <a-descriptions-item label="景点总数">
            {{ tripPlan.days.reduce((s, d) => s + d.attractions.length, 0) }}
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- 预算 -->
      <a-card v-if="tripPlan.budget" id="budget" title="💰 预算明细" class="section-card" :bordered="false">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-statistic title="景点门票" :value="tripPlan.budget.total_attractions" suffix="元" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="酒店住宿" :value="tripPlan.budget.total_hotels" suffix="元" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="餐饮费用" :value="tripPlan.budget.total_meals" suffix="元" />
          </a-col>
          <a-col :span="6">
            <a-statistic title="交通费用" :value="tripPlan.budget.total_transportation" suffix="元" />
          </a-col>
        </a-row>
        <a-divider />
        <a-row>
          <a-col :span="24" style="text-align: center">
            <a-statistic
              title="预估总费用"
              :value="tripPlan.budget.total"
              suffix="元"
              :value-style="{ color: '#cf1322', fontSize: '32px', fontWeight: 'bold' }"
            />
          </a-col>
        </a-row>
      </a-card>

      <!-- 地图 -->
      <a-card id="map" title="🗺️ 景点地图" class="section-card" :bordered="false">
        <div id="amap-container" style="width: 100%; height: 400px"></div>
      </a-card>

      <!-- 每日行程 -->
      <div id="days">
        <a-card
          v-for="(day, di) in tripPlan.days"
          :key="di"
          :title="`📅 第 ${day.day_index + 1} 天 · ${day.date}`"
          class="section-card day-card"
          :bordered="false"
        >
          <p class="day-desc">{{ day.description }}</p>
          <p class="day-info">🚌 {{ day.transportation }} | 🏠 {{ day.accommodation }}</p>

          <!-- 酒店 -->
          <a-alert
            v-if="day.hotel"
            type="info"
            show-icon
            class="hotel-alert"
          >
            <template #message>
              🏨 {{ day.hotel.name }} ·
              {{ day.hotel.price_range }} ·
              ⭐ {{ day.hotel.rating }}
            </template>
          </a-alert>

          <!-- 景点列表 -->
          <div class="attraction-list">
            <a-card
              v-for="(attr, ai) in day.attractions"
              :key="ai"
              class="attraction-item"
              :bordered="true"
              size="small"
            >
              <a-row align="middle" :gutter="16">
                <a-col :span="4">
                  <div class="image-container">
                    <img
                      v-if="attr.image_url"
                      :src="attr.image_url"
                      :alt="attr.name"
                      class="attraction-img"
                      @error="handleImageError($event, attr)"
                      @load="handleImageLoad($event)"
                    />
                    <div v-if="!attr.image_url" class="attraction-img-placeholder">🖼️</div>
                  </div>
                </a-col>
                <a-col :span="editMode ? 14 : 18">
                  <h4>{{ attr.name }}
                    <a-tag color="blue" v-if="attr.category">{{ attr.category }}</a-tag>
                  </h4>
                  <p class="attr-addr">📍 {{ attr.address }}</p>
                  <p class="attr-desc">{{ attr.description }}</p>
                  <p class="attr-meta">
                    ⏱️ {{ attr.visit_duration }}分钟 |
                    🎫 {{ attr.ticket_price }}元 |
                    ⭐ {{ attr.rating ?? '暂无评分' }}
                  </p>
                </a-col>
                <a-col :span="editMode ? 6 : 0" v-if="editMode">
                  <a-space direction="vertical" size="small">
                    <a-button size="small" @click="moveAttraction(di, ai, 'up')" :disabled="ai === 0">⬆ 上移</a-button>
                    <a-button size="small" @click="moveAttraction(di, ai, 'down')" :disabled="ai === day.attractions.length - 1">⬇ 下移</a-button>
                    <a-button size="small" danger @click="deleteAttraction(di, ai)">🗑️ 删除</a-button>
                  </a-space>
                </a-col>
              </a-row>
            </a-card>
          </div>

          <!-- 餐饮 -->
          <div class="meals-section">
            <a-tag
              v-for="meal in day.meals"
              :key="meal.type"
              :color="meal.type === 'breakfast' ? 'orange' : meal.type === 'lunch' ? 'green' : 'purple'"
            >
              {{ meal.type === 'breakfast' ? '🌅 早餐' : meal.type === 'lunch' ? '☀️ 午餐' : '🌙 晚餐' }}:
              {{ meal.name }}
              <template v-if="meal.estimated_cost">(~{{ meal.estimated_cost }}元)</template>
            </a-tag>
          </div>

          <!-- 编辑模式按钮 -->
          <div v-if="editMode" class="edit-actions">
            <a-button danger @click="deleteDay(di)">删除这一天</a-button>
          </div>
        </a-card>
      </div>

      <!-- 天气 -->
      <a-card v-if="tripPlan.weather_info?.length" id="weather" title="🌤️ 天气预报" class="section-card" :bordered="false">
        <a-row :gutter="12">
          <a-col :span="Math.min(8, Math.floor(24 / tripPlan.weather_info.length))" v-for="w in tripPlan.weather_info" :key="w.date">
            <a-card size="small" class="weather-card">
              <p class="weather-date">{{ w.date }}</p>
              <p>☀️ {{ w.day_weather }} | {{ w.day_temp }}°C</p>
              <p>🌙 {{ w.night_weather }} | {{ w.night_temp }}°C</p>
              <p>🌬️ {{ w.wind_direction }} {{ w.wind_power }}</p>
            </a-card>
          </a-col>
        </a-row>
      </a-card>

      <!-- 建议 -->
      <a-card id="suggestions" title="💡 旅行建议" class="section-card" :bordered="false">
        <p style="white-space: pre-wrap; line-height: 1.8">{{ tripPlan.overall_suggestions }}</p>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { TripPlan, Attraction } from '@/types'

const router = useRouter()

// 从路由 state 获取数据
const tripPlan = ref<TripPlan>(history.state?.tripPlan)
if (!tripPlan.value) {
  // 如果没有数据则返回首页
  router.replace('/')
}

const editMode = ref(false)
const activeSection = ref('overview')
let mapInstance: any = null

// 图片加载处理
const handleImageError = (event: Event, attr: Attraction) => {
  const img = event.target as HTMLImageElement
  console.warn(`图片加载失败: ${attr.name}`, img.src)
  // 隐藏失败的图片，显示占位符
  img.style.display = 'none'
  const placeholder = img.parentElement?.querySelector('.attraction-img-placeholder')
  if (placeholder) {
    ;(placeholder as HTMLElement).style.display = 'flex'
  }
}

const handleImageLoad = (event: Event) => {
  const img = event.target as HTMLImageElement
  // 确保图片加载成功后显示
  img.style.display = 'block'
  const placeholder = img.parentElement?.querySelector('.attraction-img-placeholder')
  if (placeholder) {
    ;(placeholder as HTMLElement).style.display = 'none'
  }
}

// ── 地图初始化 ──
const initMap = async () => {
  await nextTick()
  const container = document.getElementById('amap-container')
  if (!container || !tripPlan.value) return

  try {
    const AMapLoader = (await import('@amap/amap-jsapi-loader')).default
    const AMap = await AMapLoader.load({
      key: '84d817fc02945b54dbb2dc1f2ece2bd7', // 高德地图 Web 端 JS Key
      version: '2.0',
    })

    if (mapInstance) mapInstance.destroy()
    mapInstance = new AMap.Map('amap-container', {
      zoom: 12,
      center: [116.397128, 39.916527],
    })

    // 收集所有景点坐标用于自动缩放
    const markers: any[] = []
    let idx = 0
    tripPlan.value.days.forEach((day) => {
      day.attractions.forEach((attraction) => {
        const pos: [number, number] = [attraction.location.longitude, attraction.location.latitude]
        const marker = new AMap.Marker({
          position: pos,
          title: attraction.name,
          label: { content: `${idx + 1}`, direction: 'top' },
        })
        markers.push(marker)
        idx++
      })
    })

    mapInstance.add(markers)
    if (markers.length > 0) {
      mapInstance.setFitView(markers)
    }
  } catch (e) {
    console.warn('地图加载失败（需要配置高德 Web JS Key）:', e)
  }
}

// ── 侧边导航 ──
const scrollToSection = ({ key }: { key: string }) => {
  activeSection.value = key
  const el = document.getElementById(key)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ── 编辑功能 ──
const originalPlan = ref<TripPlan | null>(null)

const toggleEditMode = () => {
  if (!editMode.value) {
    originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
    editMode.value = true
  } else {
    editMode.value = false
    message.success('修改已保存')
    initMap()
  }
}

const moveAttraction = (dayIndex: number, attrIndex: number, direction: 'up' | 'down') => {
  const attractions = tripPlan.value!.days[dayIndex].attractions
  const newIndex = direction === 'up' ? attrIndex - 1 : attrIndex + 1
  if (newIndex >= 0 && newIndex < attractions.length) {
    ;[attractions[attrIndex], attractions[newIndex]] = [attractions[newIndex], attractions[attrIndex]]
  }
}

const deleteAttraction = (dayIndex: number, attrIndex: number) => {
  tripPlan.value!.days[dayIndex].attractions.splice(attrIndex, 1)
}

const deleteDay = (dayIndex: number) => {
  tripPlan.value!.days.splice(dayIndex, 1)
  // 重新编号
  tripPlan.value!.days.forEach((d, i) => (d.day_index = i))
}

// ── 导出功能 ──
const exportAsImage = async () => {
  try {
    const html2canvas = (await import('html2canvas')).default
    const el = document.getElementById('trip-plan-content')
    if (!el) return
    const canvas = await html2canvas(el, { backgroundColor: '#f0f2f5', scale: 2, useCORS: true })
    const link = document.createElement('a')
    link.download = `${tripPlan.value!.city}旅行计划.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    message.success('导出成功！')
  } catch (e) {
    message.error('导出失败')
  }
}

const exportAsPDF = async () => {
  try {
    const html2canvas = (await import('html2canvas')).default
    const jsPDF = (await import('jspdf')).default
    const el = document.getElementById('trip-plan-content')
    if (!el) return
    const canvas = await html2canvas(el, { backgroundColor: '#ffffff', scale: 2, useCORS: true })
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const imgWidth = 210
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)
    pdf.save(`${tripPlan.value!.city}旅行计划.pdf`)
    message.success('导出成功！')
  } catch (e) {
    message.error('导出失败')
  }
}

onMounted(() => {
  initMap()
})
</script>

<style scoped>
.result-container {
  display: flex;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  gap: 24px;
}

.side-nav {
  width: 180px;
  flex-shrink: 0;
}

.side-nav :deep(.ant-menu) {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.main-content {
  flex: 1;
  min-width: 0;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.header-bar h2 {
  margin: 0;
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.section-card {
  margin-bottom: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.day-card {
  margin-bottom: 20px;
}

.day-desc {
  color: #595959;
  font-style: italic;
  margin-bottom: 8px;
}

.day-info {
  color: #8c8c8c;
  font-size: 13px;
}

.hotel-alert {
  margin: 12px 0;
}

.attraction-list {
  margin-top: 12px;
}

.attraction-item {
  margin-bottom: 12px;
  border-radius: 8px;
  transition: box-shadow 0.2s;
}

.attraction-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.image-container {
  position: relative;
  width: 100%;
  height: 80px;
}

.attraction-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
  display: block;
}

.attraction-img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 28px;
}

.attr-addr {
  color: #8c8c8c;
  font-size: 12px;
  margin: 4px 0;
}

.attr-desc {
  color: #595959;
  margin: 4px 0;
}

.attr-meta {
  color: #faad14;
  font-size: 13px;
  margin: 4px 0;
}

.meals-section {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.edit-actions {
  margin-top: 12px;
  text-align: right;
}

.weather-card {
  text-align: center;
  border-radius: 8px;
}

.weather-date {
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 8px;
}
</style>
