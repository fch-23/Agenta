<template>
  <div class="ai-editor-layout">

    <!-- 编辑器区：两个编辑器上下排列 -->
    <div class="editor-panel">
      <div class="editors-double">
        <!-- 转写编辑器块，支持折叠/展开 -->
        <div class="editor-block" :class="{ 'transcribe-collapsed': transcribeCollapsed }">
          <div class="editor-label transcribe-label" @click="transcribeCollapsed = !transcribeCollapsed"
            style="cursor:pointer;user-select:none;">
            <span :class="['triangle', transcribeCollapsed ? '' : 'expanded']">&#9654;</span>
            转写
          </div>
          <transition name="fade">
            <div v-show="!transcribeCollapsed" class="editor-content-fixed">
              <editor-content :editor="transcribeEditor" />
            </div>
          </transition>
        </div>
        <div class="hint">💡 请选择需要优化的文本</div>
        <!-- 会议纪要 -->
        <div class="editor-block" :class="{ 'main-expanded': transcribeCollapsed }">
          <div class="editor-label">会议纪要</div>
          <div class="editor-content-fixed">
            <div v-if="showMarkdownPreview" class="markdown-preview" v-html="markdownHtml"></div>
            <editor-content v-else :editor="editor" />
            <div class="editor-actions">
              <button class="preview-toggle-btn" @click="showMarkdownPreview = !showMarkdownPreview">
                {{ showMarkdownPreview ? '编辑' : '预览' }}
              </button>
              <button class="save-btn" @click="saveMeetingNote">保存</button>
            </div>
          </div>
        </div>
      </div>
      <div class="button-group" style="margin-top: 18px;">
        <button @click="runAiCommand('rephrase')" :disabled="isDisabled">改写</button>
        <button @click="runAiCommand('summarize')" :disabled="isDisabled">总结</button>
        <button @click="runAiCommand('simplify')" :disabled="isDisabled">简化</button>
        <button @click="runAiCommand('fixSpelling')" :disabled="isDisabled">纠正拼写</button>
        <button @click="runAiCommand('translateChinese')" :disabled="isDisabled">翻译为中文</button>
        <button @click="runAiCommand('translateEnglish')" :disabled="isDisabled">翻译为英语</button>
      </div>
      <div v-if="state.errorMessage" class="hint error">{{ state.errorMessage }}</div>
      <div v-if="editor && editor.isEmpty" class="editor-placeholder">
        请在下方编辑区输入或粘贴文本
      </div>
    </div>

    <!-- 右侧AI结果 -->
    <div class="ai-result-panel">
      <div class="ai-result-title">AI辅助优化</div>
      <div class="ai-chat-history-scroll">
        <!-- ...历史对话区内容不变... -->
        <template v-if="chatHistory.length > 0">
          <div v-for="(item, idx) in chatHistory" :key="idx" class="chat-item">
            <div class="chat-row single">
              <div class="chat-user-side">
                <div class="chat-bubble user">
                  <div class="chat-user"></div>
                  <div>{{ item.user }}</div>
                </div>
              </div>
            </div>
            <div class="chat-row single">
              <div class="chat-ai-side">
                <div class="chat-bubble ai">
                  <div class="chat-ai"></div>
                  <div>{{ item.ai }}</div>
                </div>
                <div class="chat-actions left">
                  <button @click="replaceSelectionFromHistory(idx)" :disabled="!item.ai">替代</button>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="ai-empty-hint">
            <div class="ai-empty-icon">
              <!-- 你可以替换为更合适的SVG图标 -->
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="32" fill="#f7faf7" />
                <path d="M20 44v-2a8 8 0 0 1 8-8h8a8 8 0 0 1 8 8v2" stroke="#95c11f" stroke-width="2"
                  stroke-linecap="round" />
                <circle cx="24" cy="28" r="2" fill="#95c11f" />
                <circle cx="40" cy="28" r="2" fill="#95c11f" />
                <path d="M28 36c1.5 2 6.5 2 8 0" stroke="#95c11f" stroke-width="2" stroke-linecap="round" />
              </svg>
            </div>
            <div class="ai-empty-text">
              说点什么吧！让AI来帮助你理解会议
            </div>
          </div>
        </template>
        <div v-if="state.isLoading" class="hint purple-spinner" style="text-align:center;margin:8px 0;">
          AI 正在生成中……
        </div>
      </div>
      <div>
        <div v-if="selectedTextForPrompt" class="selected-bubble">
          <span>选中内容：</span>
          <div class="chat-bubble user">{{ selectedTextForPrompt }}</div>
        </div>
        <div class="ai-custom-prompt">
          <input v-model="customPrompt" type="text" placeholder="请输入你的问题或需求" @keyup.enter="sendCustomPrompt" />
          <button @click="sendCustomPrompt" :disabled="!customPrompt || state.isLoading">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import StarterKit from '@tiptap/starter-kit'
import { Editor, EditorContent } from '@tiptap/vue-3'
import OpenAI from 'openai'
import { Plugin } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'
import { defineComponent } from 'vue'
import { marked } from 'marked' // 需安装 marked 库：npm install marked

export default defineComponent({
  components: {
    EditorContent,
  },

  data() {
    return {
      state: {
        isLoading: false,
        errorMessage: null,
        response: null,
      },
      editor: null,
      transcribeEditor: null,
      openai: null,
      apiKey: 'sk-8557191220f74fc4bc2e919eb1e8147b',
      highlightRange: null,
      customPrompt: '',
      chatHistory: [],
      transcribeCollapsed: true, // 默认折叠
      showMarkdownPreview: false,
      meetingData: {
        transcribe: '',
        note: '',
      },
    }
  },

  computed: {
    isDisabled() {
      if (!this.editor) return true
      // 检查编辑器是否有内容
      return this.editor.isEmpty
    },
    selectedTextForPrompt() {
      if (!this.editor) return ''
      return this.editor.state.doc.textBetween(
        this.highlightRange?.from || 0,
        this.highlightRange?.to || this.editor.state.doc.content.size
      )
    },
    markdownHtml() {
      if (!this.editor) return ''
      // 获取纯文本内容并去除多余的 <p> 标签
      const raw = this.editor.getHTML()
      // 提取编辑器内容中的纯 markdown 部分
      // 这里假设内容是 <p>...</p> 包裹的 markdown
      // 可以用正则去除所有 <p> 标签
      const markdownText = raw
        .replace(/<\/?p>/g, '\n')
        .replace(/<br\s*\/?>/g, '\n')
        .replace(/<\/?strong>/g, '**')
        .replace(/<\/?em>/g, '*')
        .replace(/<\/?u>/g, '')
        .replace(/<\/?s>/g, '~~')
        .replace(/<\/?ul>/g, '')
        .replace(/<\/?ol>/g, '')
        .replace(/<\/?li>/g, '\n- ')
        .replace(/<\/?h[1-6]>/g, '\n')
        .replace(/&nbsp;/g, ' ')
        .replace(/<[^>]+>/g, '') // 去除其它标签
        .trim()
      return marked.parse(markdownText)
    }
  },

  methods: {
    // 新增方法：获取summary.md
    async fetchSummaryMd() {
      try {
        const response = await fetch('/summary.md') // 假设前后端同域，不同域需用完整URL
        if (!response.ok) throw new Error('获取summary.md失败')
        const markdownContent = await response.text()
        // 将内容设置到会议纪要编辑器
        this.editor?.commands.setContent(markdownContent)
      } catch (error) {
        console.error('加载summary.md出错:', error)
        this.state.errorMessage = '加载会议纪要失败，请稍后重试'
      }
    },

    initOpenAI() {
      if (!this.apiKey) return
      this.openai = new OpenAI({
        apiKey: this.apiKey,
        baseURL: 'https://api.deepseek.com/v1',
        dangerouslyAllowBrowser: true,
      })
    },

    // 新增：自动选择全文的方法
    selectAllText() {
      if (!this.editor) return
      const { doc } = this.editor.state
      // 只在需要AI处理时自动选中全文，不影响用户正常选区
      this.highlightRange = { from: 0, to: doc.content.size }
    },

    async runAiCommand(command) {
      if (!this.editor || !this.openai) return

      // 获取当前选区
      const { from, to } = this.editor.state.selection
      let selectedText = this.editor.state.doc.textBetween(from, to)

      // 如果没有选中内容，仅用于AI处理，不改变编辑器选区
      let highlightFrom = from, highlightTo = to
      if (from === to) {
        selectedText = this.editor.getText().trim()
        // highlightRange 只用于高亮和替代，不影响实际选区
        highlightFrom = 0
        highlightTo = this.editor.state.doc.content.size
      }
      this.highlightRange = (from !== to || selectedText) ? { from: highlightFrom, to: highlightTo } : null

      const commandMap = {
        keypoints: '提取要点', rephrase: '改写', summarize: '总结', simplify: '简化',
        fixSpelling: '纠正拼写', continueWriting: '续写', emojify: '添加表情',
        deEmojify: '移除表情', translateChinese: '翻译为中文', translateEnglish: '翻译为英语'
      }
      const userQuestion = `请帮我${commandMap[command]}${from !== to ? '（针对选中内容）' : '（针对全文）'}`
      let prompt = ''
      switch (command) {
        case 'rephrase': prompt = `用不同的表达方式重写以下文本：\n\n${selectedText}`; break
        case 'summarize': prompt = `总结以下文本的主要内容：\n\n${selectedText}`; break
        case 'simplify': prompt = `简化以下文本，使其更容易理解：\n\n${selectedText}`; break
        case 'fixSpelling': prompt = `修正以下文本中的拼写和语法错误：\n\n${selectedText}`; break
        case 'translateChinese': prompt = `将以下文本翻译成中文：\n\n${selectedText}`; break
        case 'translateEnglish': prompt = `将以下文本翻译成英语：\n\n${selectedText}`; break
      }
      try {
        this.state.isLoading = true
        this.state.errorMessage = null
        const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}`,
          },
          body: JSON.stringify({
            model: 'deepseek-chat',
            messages: [
              { role: 'system', content: '你是一个智能写作助手，帮助用户处理文本。请只返回普通文本，不要使用markdown格式，如果用户不要求翻译，原文使用哪种语言，返回文本使用哪种语言。' },
              { role: 'user', content: prompt }
            ],
            temperature: 0.7,
            max_tokens: 1000,
          }),
        })
        const data = await response.json()
        if (!data.choices || !Array.isArray(data.choices) || !data.choices[0]) {
          this.state.errorMessage = data.error?.message || 'AI接口返回异常，请检查API Key和配额'
          this.state.isLoading = false
          return
        }
        const aiResponse = data.choices[0].message.content
        this.state.response = aiResponse
        this.chatHistory.push({ user: userQuestion, ai: aiResponse })
      } catch (error) {
        this.state.errorMessage = `AI处理失败: ${error.message}`
      } finally {
        this.state.isLoading = false
      }
    },

    async sendCustomPrompt() {
      if (!this.customPrompt) return
      this.state.isLoading = true
      this.state.errorMessage = null

      // 获取当前选区
      const { from, to } = this.editor.state.selection
      let selectedText = this.editor.state.doc.textBetween(from, to)

      // 如果没有选中内容，仅用于AI处理，不改变编辑器选区
      let highlightFrom = from, highlightTo = to
      if (from === to) {
        selectedText = this.editor.getText().trim()
        // highlightRange 只用于高亮和替代，不影响实际选区
        // highlightFrom = 0
        // highlightTo = this.editor.state.doc.content.size
      }
      // 保持原选区，不自动变为全文
      this.highlightRange = (from !== to || selectedText) ? { from: highlightFrom, to: highlightTo } : null

      let prompt = selectedText
        ? `针对以下文本片段，${this.customPrompt}\n\n${selectedText}`
        : this.customPrompt

      try {
        const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}`,
          },
          body: JSON.stringify({
            model: 'deepseek-chat',
            messages: [
              { role: 'system', content: '你是一个智能写作助手，帮助用户处理文本。请只返回普通文本，不要使用markdown格式。' },
              { role: 'user', content: prompt }
            ],
            temperature: 0.7,
            max_tokens: 1000,
          }),
        })
        const data = await response.json()
        if (!data.choices || !Array.isArray(data.choices) || !data.choices[0]) {
          this.state.errorMessage = data.error?.message || 'AI接口返回异常，请检查API Key和配额'
          this.state.isLoading = false
          return
        }
        const aiResponse = data.choices[0].message.content
        this.state.response = aiResponse
        this.chatHistory.push({
          user: this.customPrompt + (selectedText ? `（针对选中内容）` : ''),
          ai: aiResponse,
        })
        this.customPrompt = ''
      } catch (error) {
        this.state.errorMessage = `AI处理失败: ${error.message}`
      } finally {
        this.state.isLoading = false
      }
    },

    replaceSelectionFromHistory(idx) {
      const historyItem = this.chatHistory[idx]
      if (!this.editor || !this.highlightRange || !historyItem.ai) return
      const { from, to } = this.highlightRange
      historyItem.originalText = this.editor.state.doc.textBetween(from, to)
      this.editor.chain().focus().deleteRange({ from, to }).insertContent(historyItem.ai).run()
      this.state.response = ''
      this.highlightRange = null
      historyItem.replaced = true
    },

    undoReplaceFromHistory(idx) {
      const historyItem = this.chatHistory[idx]
      if (!this.editor || !this.highlightRange || !historyItem.originalText) return
      const { from, to } = this.highlightRange
      this.editor.chain().focus().deleteRange({ from, to }).insertContent(historyItem.originalText).run()
      historyItem.replaced = false
    },

    discardHistory(idx) {
      this.chatHistory.splice(idx, 1)
    },

    // 读取
    async fetchMeetingData() {
      const res = await fetch('http://localhost:3001/api/meeting')
      const data = await res.json()
      this.transcribeEditor?.commands.setContent(data.transcribe || '')
      this.editor?.commands.setContent(data.note || '')
    },

    // 保存
    async saveMeetingNote() {
      const transcribe = this.transcribeEditor?.getText() || ''
      const note = this.editor?.getText() || ''
      await fetch('http://localhost:3001/api/meeting', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcribe, note })
      })
      alert('会议纪要已保存！')
    },
  },

  watch: {
    chatHistory() {
      this.$nextTick(() => {
        const chatScroll = this.$el.querySelector('.ai-chat-history-scroll')
        if (chatScroll) chatScroll.scrollTop = chatScroll.scrollHeight
      })
    },
    'editor.state.selection'() {
      const { from, to } = this.editor.state.selection
      this.highlightRange = from !== to ? { from, to } : null
    }
  },

  mounted() {
    this.initOpenAI()
    this.fetchSummaryMd()
    this.fetchMeetingData()
    this.editor = new Editor({
      extensions: [
        StarterKit,
        new Plugin({
          props: {
            decorations: () => null
          }
        })
      ],
      content: `
        <p>

# 会议纪要：项目凤凰第三阶段启动会

## 📅 会议基本信息
| 项目         | 内容                     |
|--------------|--------------------------|
| **会议主题** | 凤凰项目第三阶段任务分配 |
| **会议时间** | 2025-08-04 14:00-15:30   |
| **会议形式** | 线上（腾讯会议：888 999 000） |
| **主持人**   | 张伟（项目经理）         |
| **记录人**   | 李明（项目助理）         |

## 👥 参会人员
**出席：**  
✅ 张伟、王芳（技术）、李磊（前端）、陈静（后端）、刘洋（UI）、赵敏（测试）  
**缺席：**  
❌ 孙涛（产品，请假）

---

## 📌 议程与讨论摘要

### 1. 阶段二总结（14:00-14:15）
- 核心模块 A/B 已上线，用户反馈良好
- **遗留问题**：3 个低优先级 Bug（测试组跟进）

</p >
      `,
    })
    this.transcribeEditor = new Editor({
      extensions: [StarterKit],
      content: '',
    })
    this.editor.registerPlugin(new Plugin({
      props: {
        decorations: (state) => {
          if (!this.highlightRange) return null
          const { from, to } = this.highlightRange
          return DecorationSet.create(state.doc, [
            Decoration.inline(from, to, { class: 'ai-highlight' })
          ])
        }
      }
    }))
    this.$nextTick(() => {
      const chatScroll = this.$el.querySelector('.ai-chat-history-scroll')
      if (chatScroll) chatScroll.scrollTop = chatScroll.scrollHeight
    })
    this.fetchMeetingData()
  },

  beforeUnmount() {
    this.editor.destroy()
  },
})
</script>

<style lang="scss" scoped>
$main-green: #95c11f;
$main-green-light: #f7faf7;
$main-green-dark: #195c3e;
$main-green-mid: #b7e28a;
$sidebar-width: 220px;

.ai-editor-layout {
  display: flex;
  background: $main-green-light;
  height: 100%;
  width: 100%;
  font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
  min-height: 0;
  overflow: hidden;
}

aside {
  width: $sidebar-width;
  background: #fff;
  border-right: 1px solid #e5eaf3;
  display: flex;
  flex-direction: column;
  height: 100vh;
  box-shadow: 0 2px 12px rgba(149, 193, 31, 0.06);

  .sidebar-item {
    background: $main-green-light;
    border-radius: 8px;
    padding: 10px 16px;
    color: $main-green;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;

    &:hover,
    &.active {
      background: $main-green-mid;
      color: $main-green-dark;
    }

    i {
      color: $main-green;
    }
  }
}

.editor-panel {
  flex: 2 1 0;
  min-width: 0;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(149, 193, 31, 0.08);
  padding: 32px 32px 24px 32px;
  margin: 24px 0 24px 24px;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.editors-double {
  display: flex;
  flex-direction: column;
  gap: 24px;
  flex: 1 1 0;
}

.editor-block {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  background: #f7faf7;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.04);
  padding: 18px 16px;
  transition: flex 0.3s, max-height 0.3s;

  &.transcribe-collapsed {
    flex: 0 0 auto;
    max-height: 38px;
    padding-bottom: 0;
    padding-top: 0;
    background: transparent;
    box-shadow: none;
    border-radius: 12px 12px 0 0;
  }

  &.main-expanded {
    flex: 1 1 auto;
  }
}

.editor-label {
  font-weight: bold;
  font-size: 17px;
  color: $main-green-dark;
  margin-bottom: 10px;
  letter-spacing: 1px;
}

.editor-content-fixed {
  flex: 1 1 0;
  min-height: 0;
  height: 100%;
  width: 100%;
  overflow-y: auto;
  border-radius: 10px;
  border: none;
  background: transparent;
  margin-bottom: 0;
  box-shadow: none;
  position: relative;
  display: flex;
  flex-direction: column;

  >.tiptap-editor,
  >.ProseMirror {
    flex: 1 1 0;
    width: 100%;
    min-height: 0;
    height: 100%;
    box-sizing: border-box;
    background: transparent;
    border: none;
    margin: 0;
    padding: 0;
    overflow-y: auto;
    display: block;
  }
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 18px 0 0 0;

  button {
    background: $main-green;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
    box-shadow: 0 2px 8px rgba(149, 193, 31, 0.08);

    &:disabled {
      background: #e5eaf3;
      color: #aaa;
      cursor: not-allowed;
    }
  }
}

.hint {
  margin-bottom: 12px;
  font-size: 15px;
  color: $main-green-dark;

  &.error {
    color: #d93025;
    background: #fff0f0;
    border-radius: 6px;
    padding: 6px 12px;
  }

  &.purple-spinner {
    font-weight: bold;
  }
}

.editor-placeholder {
  color: #bbb;
  padding: 18px;
  text-align: center;
  position: absolute;
  width: 100%;
  pointer-events: none;
  z-index: 1;
  font-size: 16px;
  background: $main-green-light;
  border-radius: 8px;
}

.ai-result-panel {
  flex: 1 1 0;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(149, 193, 31, 0.08);
  padding: 32px 32px 24px 32px;
  margin: 24px 24px 24px 0;
  position: relative;
  min-height: 0;
  overflow: hidden;
}

.ai-result-title {
  font-weight: bold;
  font-size: 20px;
  margin-bottom: 8px;
  color: $main-green-dark;
  letter-spacing: 1px;
}

.ai-highlight {
  background: #c8e6c9 !important;
}

.ai-chat-history-scroll {
  flex: 1 1 0;
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  padding-right: 4px;
  margin-bottom: 12px;
  scrollbar-width: thin;
  scrollbar-color: $main-green $main-green-light;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.04);

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-thumb {
    background: $main-green;
    border-radius: 8px;
  }

  &::-webkit-scrollbar-track {
    background: $main-green-light;
    border-radius: 8px;
  }
}

.chat-item {
  margin-bottom: 10px;
}

.chat-row {
  display: flex;
  justify-content: flex-start;
  align-items: flex-end;
  gap: 16px;
}

.chat-user-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  max-width: 60%;
  margin-left: auto;
}

.chat-ai-side {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 60%;
}

.chat-bubble {
  position: relative;
  padding: 10px 16px;
  border-radius: 18px;
  margin-bottom: 4px;
  max-width: 100%;
  word-break: break-all;
  font-size: 15px;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.04);

  &.ai {
    background: #f7f7f7;
    color: $main-green-dark;
    border-bottom-left-radius: 4px;
    border-top-left-radius: 0;
    margin-left: 8px;
    align-self: flex-start;

    &::before {
      content: "";
      position: absolute;
      left: -8px;
      top: 16px;
      border-width: 8px 10px 8px 0;
      border-style: solid;
      border-color: transparent #f7f7f7 transparent transparent;
    }
  }

  &.user {
    background: $main-green;
    color: #fff;
    border-bottom-right-radius: 4px;
    border-top-right-radius: 0;
    margin-right: 8px;
    align-self: flex-end;

    &::before {
      content: "";
      position: absolute;
      right: -8px;
      top: 16px;
      border-width: 8px 0 8px 10px;
      border-style: solid;
      border-color: transparent transparent transparent $main-green;
    }
  }
}

.chat-actions {
  display: flex;
  gap: 8px;
  margin-top: 2px;

  &.left {
    justify-content: flex-start;
  }

  button {
    background: $main-green-light;
    color: $main-green-dark;
    border: none;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 14px;
    cursor: pointer;
    box-shadow: 0 1px 4px rgba(149, 193, 31, 0.06);
    transition: background 0.2s;

    &:disabled {
      background: #e5eaf3;
      color: #aaa;
      cursor: not-allowed;
    }
  }
}

.selected-bubble {
  margin-bottom: 10px;
  font-size: 14px;
  color: $main-green-dark;
  display: flex;
  align-items: center;

  .chat-bubble.user {
    display: inline-block;
    margin-left: 8px;
    background: $main-green-light;
    padding: 7px 14px;
    border-radius: 12px;
    max-width: 80%;
    word-break: break-all;
    font-size: 15px;
    box-shadow: 0 2px 8px rgba(149, 193, 31, 0.04);
    color: $main-green-dark;
    max-height: 4.5em;
    overflow-y: auto;
  }
}

.ai-custom-prompt {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;

  input {
    flex: 1;
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid $main-green-mid;
    font-size: 15px;
    background: $main-green-light;
    box-shadow: 0 2px 8px rgba(149, 193, 31, 0.04);
    color: $main-green-dark;
  }

  button {
    padding: 8px 20px;
    border-radius: 8px;
    background: linear-gradient(90deg, $main-green 60%, $main-green-mid 100%);
    color: #fff;
    border: none;
    cursor: pointer;
    font-size: 15px;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(149, 193, 31, 0.08);
    transition: background 0.2s;

    &:disabled {
      background: #e5eaf3;
      color: #aaa;
      cursor: not-allowed;
    }
  }
}

.transcribe-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.triangle {
  display: inline-block;
  transition: transform 0.2s;
  font-size: 15px;

  &.expanded {
    transform: rotate(90deg);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.ai-empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 80%;
  color: #b7e28a;
  user-select: none;
  pointer-events: none;

  .ai-empty-icon {
    margin-bottom: 18px;
  }

  .ai-empty-text {
    font-size: 18px;
    color: #95c11f;
    font-weight: 500;
    letter-spacing: 1px;
    text-align: center;
  }
}

.markdown-preview {
  margin-top: 0;
  padding: 0;
  background: transparent;
  border-radius: 0;
  border: none;
  font-size: 15px;
  color: #333;
  height: 100%;
  max-height: none;
  overflow: auto;
  width: 100%;
  box-shadow: none;
}

.editor-actions {
  position: absolute;
  right: 16px;
  bottom: 16px;
  display: flex;
  gap: 10px;
  z-index: 2;
}

.preview-toggle-btn {
  background: $main-green;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 5px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.08);
  transition: background 0.2s;
  margin: 0;

  &:hover {
    background: $main-green-dark;
  }
}

.save-btn {
  background: $main-green;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 5px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.08);
  transition: background 0.2s;
  margin: 0;

  &:hover {
    background: $main-green-dark;
  }
}
</style>