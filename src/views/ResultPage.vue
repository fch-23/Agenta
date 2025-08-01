<template>
  <div class="p-6 md:p-8">
    <!-- 标题区域 -->
    <div class="mb-8 text-center">
      <h2 class="text-2xl font-bold">生成纪要</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="max-w-4xl mx-auto">
      <div class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p class="text-neutral">正在生成会议纪要，请稍候...</p>
      </div>
    </div>

    <!-- 结果内容 -->
    <div v-else-if="summaryContent" class="max-w-4xl mx-auto">
      <div class="bg-white rounded-xl shadow-soft p-8">
        <div 
          class="markdown-content"
          v-html="renderedContent"
        ></div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-between items-center mt-8">
        <button @click="goBack" class="btn-secondary">
          返回
        </button>
        <div class="flex gap-3">
          <button @click="exportMarkdown" class="btn-secondary">
            <i class="fa fa-download mr-2"></i>
            导出Markdown
          </button>
          <button @click="exportPDF" class="btn-primary">
            <i class="fa fa-file-pdf-o mr-2"></i>
            导出PDF
          </button>
        </div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="max-w-4xl mx-auto">
      <div class="text-center py-12">
        <i class="fa fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
        <p class="text-neutral mb-4">{{ error }}</p>
        <button @click="retryGeneration" class="btn-primary">
          重试
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { marked } from 'marked'
import hljs from 'highlight.js'

export default {
  name: 'ResultPage',
  setup() {
    const router = useRouter()
    
    // 响应式数据
    const isLoading = ref(true)
    const summaryContent = ref('')
    const error = ref('')
    
    // 配置marked
    marked.setOptions({
      highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
          try {
            return hljs.highlight(code, { language: lang }).value
          } catch (err) {}
        }
        return hljs.highlightAuto(code).value
      },
      breaks: true,
      gfm: true
    })

    // 计算属性
    const renderedContent = computed(() => {
      if (!summaryContent.value) return ''
      return marked(summaryContent.value)
    })

    // 方法
    const loadSummary = async () => {
      try {
        isLoading.value = true
        error.value = ''
        
        const response = await axios.get('/api/summary.md')
        summaryContent.value = response.data
        isLoading.value = false
      } catch (err) {
        console.error('加载纪要失败:', err)
        error.value = '加载会议纪要失败，请重试'
        isLoading.value = false
      }
    }

    const retryGeneration = () => {
      loadSummary()
    }

    const goBack = () => {
      router.push('/templates')
    }

    const exportMarkdown = () => {
      if (!summaryContent.value) {
        alert('没有可导出的内容')
        return
      }

      // 创建文件名
      const now = new Date()
      const fileName = `会议纪要_${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}_${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}.md`

      // 创建Blob对象
      const blob = new Blob([summaryContent.value], { type: 'text/markdown;charset=utf-8' })

      // 创建下载链接
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName

      // 触发下载
      document.body.appendChild(a)
      a.click()

      // 清理
      setTimeout(() => {
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }, 0)

      alert('Markdown文件已成功导出')
    }

    const exportPDF = () => {
      // 这里可以集成PDF导出库，如jsPDF或html2pdf
      alert('PDF导出功能开发中...')
    }

    // 组件挂载时加载纪要
    onMounted(() => {
      loadSummary()
    })

    return {
      isLoading,
      summaryContent,
      error,
      renderedContent,
      loadSummary,
      retryGeneration,
      goBack,
      exportMarkdown,
      exportPDF
    }
  }
}
</script>

<style scoped>
.shadow-soft {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
</style> 