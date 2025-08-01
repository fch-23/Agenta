<template>
  <div class="p-6 md:p-8">
    <!-- 标题部分 -->
    <div class="mb-6">
      <h2 class="text-3xl font-bold mb-2">新建会议</h2>
      <p class="text-neutral">上传音频文件</p>
    </div>

    <!-- 文件上传区域 -->
    <div class="max-w-3xl mx-auto">
      <div 
        ref="dropArea"
        class="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-primary transition-all duration-300"
        :class="{ 'border-primary bg-primary/5': isDragOver }"
        @drop="handleDrop"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @dragenter.prevent="isDragOver = true"
      >
        <i class="fa fa-cloud-upload text-5xl text-gray-400 mb-4"></i>
        <h3 class="text-xl font-semibold text-neutral mb-2">拖放文件到此处</h3>
        <p class="text-gray-500 mb-6">或者</p>
        <label 
          for="fileInput"
          class="inline-block bg-primary hover:bg-primary/90 text-white font-medium py-3 px-8 rounded-lg cursor-pointer transition-all duration-300 shadow-md hover:shadow-lg"
        >
          <i class="fa fa-file-o mr-2"></i>选择文件
        </label>
        <input 
          ref="fileInput"
          type="file" 
          id="fileInput" 
          class="hidden" 
          accept=".mp3,.wav,.m4a,.flac,.wma"
          @change="handleFileSelect"
        >
        <p class="text-gray-400 text-sm mt-4">支持的格式：MP3、WAV、M4A/FLAC、WMA</p>
      </div>

      <!-- 文件信息预览 -->
      <div v-if="selectedFile" class="mt-8 animate-fadeIn">
        <div class="border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <div class="bg-gray-50 px-4 py-3 flex justify-between items-center">
            <h4 class="font-medium text-neutral">{{ selectedFile.name }}</h4>
            <button 
              @click="clearFileSelection"
              class="text-gray-400 hover:text-red-500 transition-all duration-200"
            >
              <i class="fa fa-times"></i>
            </button>
          </div>
          <div class="p-4">
            <div class="flex items-center space-x-4">
              <div class="w-16 h-16 rounded-lg bg-gray-100 flex items-center justify-center">
                <i :class="fileIconClass" class="text-3xl"></i>
              </div>
              <div class="flex-grow">
                <div class="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span class="text-gray-500">大小:</span>
                    <span class="text-neutral font-medium">{{ formatBytes(selectedFile.size) }}</span>
                  </div>
                  <div>
                    <span class="text-gray-500">类型:</span>
                    <span class="text-neutral font-medium">{{ selectedFile.type || '未知类型' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 上传进度条 -->
            <div v-if="isUploading" class="mt-4">
              <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  class="bg-primary h-2.5 rounded-full transition-all duration-300" 
                  :style="{ width: uploadProgress + '%' }"
                ></div>
              </div>
              <p class="text-xs text-gray-500 mt-1 text-right">{{ Math.round(uploadProgress) }}%</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 上传按钮 -->
      <div v-if="selectedFile && !isUploading" class="mt-6 text-center animate-fadeIn">
        <button 
          @click="uploadFile"
          class="bg-primary hover:bg-primary/90 text-white font-medium py-3 px-8 rounded-lg transition-all duration-300 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mx-auto"
        >
          <i class="fa fa-upload mr-2"></i>
          <span>上传文件</span>
        </button>
      </div>

      <!-- 上传状态反馈 -->
      <div v-if="statusMessage.show" class="mb-8 animate-fadeIn">
        <div 
          class="p-4 rounded-lg flex items-center"
          :class="statusMessage.class"
        >
          <i :class="statusMessage.icon" class="mr-3 text-xl"></i>
          <p>{{ statusMessage.text }}</p>
        </div>
      </div>

      <!-- 会议名称输入区域 -->
      <div class="mb-6">
        <label class="block text-neutral mb-3">会议名称</label>
        <div class="relative">
          <input 
            v-model="meetingName"
            type="text" 
            placeholder="点击输入（非必填）"
            class="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
          >
        </div>
        <p v-if="nameSaveStatus.show" class="mt-2 text-sm" :class="nameSaveStatus.class">
          {{ nameSaveStatus.text }}
        </p>
      </div>

      <!-- 音频转写提示 -->
      <div v-if="showTranscriptionHint" class="flex justify-end animate-fadeIn">
        <button @click="goToTranscription" class="btn-primary">
          下一步
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'UploadPage',
  setup() {
    const router = useRouter()
    
    // 响应式数据
    const selectedFile = ref(null)
    const isDragOver = ref(false)
    const isUploading = ref(false)
    const uploadProgress = ref(0)
    const meetingName = ref('')
    const showTranscriptionHint = ref(false)
    const uploadedFilename = ref('')
    
    const statusMessage = ref({
      show: false,
      text: '',
      type: 'info',
      class: '',
      icon: ''
    })
    
    const nameSaveStatus = ref({
      show: false,
      text: '',
      class: ''
    })

    // 计算属性
    const fileIconClass = computed(() => {
      if (!selectedFile.value) return 'fa fa-file text-gray-400'
      
      const extension = selectedFile.value.name.split('.').pop().toLowerCase()
      const iconMap = {
        'mp3': 'fa-file-audio-o text-purple-500',
        'wav': 'fa-file-audio-o text-purple-500',
        'm4a': 'fa-file-audio-o text-purple-500',
        'flac': 'fa-file-audio-o text-purple-500',
        'wma': 'fa-file-audio-o text-purple-500'
      }
      
      return iconMap[extension] || 'fa-file text-gray-400'
    })

    // 方法
    const handleDrop = (e) => {
      e.preventDefault()
      isDragOver.value = false
      
      const files = e.dataTransfer.files
      if (files.length > 0) {
        handleFile(files[0])
      }
    }

    const handleFileSelect = (e) => {
      const files = e.target.files
      if (files.length > 0) {
        handleFile(files[0])
      }
    }

    const handleFile = (file) => {
      // 检查文件格式
      const allowedExtensions = ['mp3', 'wav', 'm4a', 'flac', 'wma']
      const fileExtension = file.name.split('.').pop().toLowerCase()
      
      if (!allowedExtensions.includes(fileExtension)) {
        showStatus('错误', '文件格式错误，请选择支持的音频格式', 'error')
        return
      }

      selectedFile.value = file
      hideStatus()
    }

    const clearFileSelection = () => {
      selectedFile.value = null
      const fileInput = document.getElementById('fileInput')
      if (fileInput) fileInput.value = ''
      hideStatus()
      showTranscriptionHint.value = false
    }

    const uploadFile = async () => {
      if (!selectedFile.value) return

      isUploading.value = true
      uploadProgress.value = 0

      const formData = new FormData()
      formData.append('file', selectedFile.value)

      try {
        const response = await axios.post('/api/upload', formData, {
          onUploadProgress: (progressEvent) => {
            if (progressEvent.lengthComputable) {
              uploadProgress.value = (progressEvent.loaded / progressEvent.total) * 100
            }
          }
        })

        if (response.data.success) {
          showStatus('成功', response.data.message, 'success')
          uploadedFilename.value = response.data.filename
          showTranscriptionHint.value = true
        } else {
          showStatus('错误', response.data.error, 'error')
        }
      } catch (error) {
        showStatus('错误', '上传失败，请重试', 'error')
        console.error('上传错误:', error)
      } finally {
        isUploading.value = false
      }
    }

    const showStatus = (title, message, type) => {
      statusMessage.value = {
        show: true,
        text: message,
        type,
        class: getStatusClass(type),
        icon: getStatusIcon(type)
      }

      // 自动隐藏成功和信息类消息
      if (type === 'success' || type === 'info') {
        setTimeout(hideStatus, 5000)
      }
    }

    const hideStatus = () => {
      statusMessage.value.show = false
    }

    const getStatusClass = (type) => {
      const classMap = {
        success: 'bg-green-50 border border-green-200 text-green-700',
        error: 'bg-red-50 border border-red-200 text-red-700',
        warning: 'bg-yellow-50 border border-yellow-200 text-yellow-700',
        info: 'bg-blue-50 border border-blue-200 text-blue-700'
      }
      return classMap[type] || classMap.info
    }

    const getStatusIcon = (type) => {
      const iconMap = {
        success: 'fa fa-check-circle text-green-500',
        error: 'fa fa-exclamation-circle text-red-500',
        warning: 'fa fa-exclamation-triangle text-yellow-500',
        info: 'fa fa-info-circle text-blue-500'
      }
      return iconMap[type] || iconMap.info
    }

    const goToTranscription = async () => {
      if (!selectedFile.value) {
        showStatus('错误', '请先上传文件', 'error')
        return
      }

      try {
        // 保存会议名称
        const formData = new FormData()
        formData.append('meeting_name', meetingName.value)
        await axios.post('/api/save_meeting_name', formData)

        // 调用后端 /api/transcribe 接口
        const filename = encodeURIComponent(uploadedFilename.value || selectedFile.value.name)
        const response = await axios.get(`/api/transcribe?filename=${filename}`)
        // 跳转到转写页面（如果后端返回页面则直接跳转）
        if (response && response.request && response.request.responseURL) {
          window.location.href = response.request.responseURL
        } else {
          // 兜底跳转
          router.push(`/transcribe?filename=${filename}`)
        }
      } catch (error) {
        console.error('转写接口调用失败:', error)
        // 即使失败也继续跳转
        const filename = encodeURIComponent(uploadedFilename.value || selectedFile.value.name)
        router.push(`/transcribe?filename=${filename}`)
      }
    }

    const formatBytes = (bytes, decimals = 2) => {
      if (bytes === 0) return '0 Bytes'

      const k = 1024
      const dm = decimals < 0 ? 0 : decimals
      const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']

      const i = Math.floor(Math.log(bytes) / Math.log(k))

      return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
    }

    return {
      selectedFile,
      isDragOver,
      isUploading,
      uploadProgress,
      meetingName,
      showTranscriptionHint,
      statusMessage,
      nameSaveStatus,
      fileIconClass,
      handleDrop,
      handleFileSelect,
      clearFileSelection,
      uploadFile,
      goToTranscription,
      formatBytes
    }
  }
}
</script> 