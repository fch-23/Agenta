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
        <!-- 将提示挪到转写框下方、纪要框上方 -->
        <div class="hint" style="margin-bottom: 0; margin-top: 8px;">💡 请选择需要优化的文本</div>
        <!-- 会议纪要 -->
        <div class="editor-block" :class="{ 'main-expanded': transcribeCollapsed }">
          <div class="editor-label">会议纪要</div>
          <div class="editor-content-fixed">
            <editor-content :editor="editor" />
          </div>
        </div>
      </div>
      <div class="button-group" style="margin-top: 18px;">
        <button @click="runAiCommand('keypoints')" :disabled="isDisabled">提取要点</button>
        <button @click="runAiCommand('rephrase')" :disabled="isDisabled">改写</button>
        <button @click="runAiCommand('summarize')" :disabled="isDisabled">总结</button>
        <button @click="runAiCommand('simplify')" :disabled="isDisabled">简化</button>
        <button @click="runAiCommand('fixSpelling')" :disabled="isDisabled">纠正拼写</button>
        <button @click="runAiCommand('continueWriting')" :disabled="isDisabled">续写</button>
        <button @click="runAiCommand('emojify')" :disabled="isDisabled">添加表情</button>
        <button @click="runAiCommand('deEmojify')" :disabled="isDisabled">移除表情</button>
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
      transcribeEditor: null, // 新增：转写编辑器
      openai: null,
      apiKey: 'sk-8557191220f74fc4bc2e919eb1e8147b', // 请替换为你的API密钥
      highlightRange: null,
      customPrompt: '',
      chatHistory: [],
      transcribeCollapsed: false, // 新增：转写编辑器折叠状态
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
    }
  },

  methods: {
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
        case 'keypoints': prompt = `提取以下文本的关键点：\n\n${selectedText}`; break
        case 'rephrase': prompt = `用不同的表达方式重写以下文本：\n\n${selectedText}`; break
        case 'summarize': prompt = `总结以下文本的主要内容：\n\n${selectedText}`; break
        case 'simplify': prompt = `简化以下文本，使其更容易理解：\n\n${selectedText}`; break
        case 'fixSpelling': prompt = `修正以下文本中的拼写和语法错误：\n\n${selectedText}`; break
        case 'continueWriting': prompt = `继续以下文本的内容：\n\n${selectedText}`; break
        case 'emojify': prompt = `在以下文本中添加适当的表情符号：\n\n${selectedText}`; break
        case 'deEmojify': prompt = `从以下文本中移除所有表情符号：\n\n${selectedText}`; break
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
    }
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
        <p>Rocking like a mobile?</p>
        <p>Did you hear about the mobile phone that joined a rock band? Yeah, it was a real smartTONE!
        It rocked the stage with its gigabytes of rhythm and had everyone calling for an encore, but
        it couldn't resist the temptation to drop a few bars and left the audience in absolute silence.
        Turns out, it wasn't quite cut out for the music industry.</p>
        <p>They say it's now pursuing a career in ringtone composition. Who knows, maybe one day it'll top
        the charts with its catchy melodies!</p>
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
  },

  beforeUnmount() {
    this.editor.destroy()
  },
})
</script>

<style lang="scss">
$main-green: #95c11f;
$main-green-light: #f7faf7;
$main-green-dark: #195c3e;
$main-green-mid: #b7e28a;
$sidebar-width: 220px;

.ai-editor-layout {
  display: flex;
  background: $main-green-light;
  /* min-height: 100vh; */
  /* height: 100vh; */
  /* width: 100vw; */
  height: 100%;
  width: 100%;
  font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

aside {
  width: $sidebar-width;
  background: #fff;
  border-right: 1px solid #e5eaf3;
  display: flex;
  flex-direction: column;
  height: 100vh;
  box-shadow: 0 2px 12px rgba(149, 193, 31, 0.06);

  .p-4,
  .md\:p-6 {
    background: #fff;
  }

  .sidebar-item {
    background: $main-green-light;
    border-radius: 8px;
    padding: 10px 16px;
    color: $main-green;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
      background: $main-green-mid;
    }

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
  /* height: calc(100vh - 48px); */
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
}

.editor-block:last-child {
  /* 主编辑器始终填满剩余空间 */
  flex: 1 1 0;
}

.editor-block.transcribe-collapsed {
  /* 折叠时高度最小，仅显示标题 */
  flex: 0 0 auto;
  max-height: 38px;
  padding-bottom: 0;
  padding-top: 0;
  background: transparent;
  box-shadow: none;
  border-radius: 12px 12px 0 0;
}

.editor-block.main-expanded {
  /* 主编辑器在转写折叠时占满空间 */
  flex: 1 1 auto;
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
  min-height: 120px;
  overflow-y: auto;
  border-radius: 10px;
  border: 1px solid $main-green-mid;
  background: #fff;
  margin-bottom: 0;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.04);
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 18px 0 0 0;
}

.button-group button {
  background: linear-gradient(90deg, $main-green 60%, $main-green-mid 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.08);
}

.button-group button:disabled {
  background: #e5eaf3;
  color: #aaa;
  cursor: not-allowed;
}

.hint {
  margin-bottom: 12px;
  font-size: 15px;
  color: $main-green-dark;
}

.hint.error {
  color: #d93025;
  background: #fff0f0;
  border-radius: 6px;
  padding: 6px 12px;
}

.hint.purple-spinner {
  color: $main-green-dark;
  font-weight: bold;
  font-size: 15px;
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
  /* height: calc(100vh - 48px); */
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
  max-height: none;
  height: 100%;
  overflow-y: auto;
  padding-right: 4px;
  margin-bottom: 12px;
  scrollbar-width: thin;
  scrollbar-color: $main-green $main-green-light;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.04);
}

.ai-chat-history-scroll::-webkit-scrollbar {
  width: 8px;
}

.ai-chat-history-scroll::-webkit-scrollbar-thumb {
  background: $main-green;
  border-radius: 8px;
}

.ai-chat-history-scroll::-webkit-scrollbar-track {
  background: $main-green-light;
  border-radius: 8px;
}

.chat-item {
  margin-bottom: 10px;
}

.chat-row {
  display: flex;
  justify-content: flex-start;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 0;
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
}

.chat-bubble.ai {
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

.chat-bubble.user {
  background: linear-gradient(90deg, $main-green 60%, $main-green-dark 100%);
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

.chat-actions {
  display: flex;
  gap: 8px;
  margin-top: 2px;
}

.chat-actions.left {
  justify-content: flex-start;
}

.chat-actions button {
  background: $main-green-light;
  color: $main-green-dark;
  border: none;
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(149, 193, 31, 0.06);
  transition: background 0.2s;
}

.chat-actions button:disabled {
  background: #e5eaf3;
  color: #aaa;
  cursor: not-allowed;
}

.selected-bubble {
  margin-bottom: 10px;
  font-size: 14px;
  color: $main-green-dark;
  display: flex;
  align-items: center;
}

.selected-bubble .chat-bubble.user {
  display: inline-block;
  margin-left: 8px;
  background: linear-gradient(90deg, $main-green-light 60%, #d0e6db 100%);
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

.ai-custom-prompt {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.ai-custom-prompt input {
  flex: 1;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid $main-green-mid;
  font-size: 15px;
  background: $main-green-light;
  box-shadow: 0 2px 8px rgba(149, 193, 31, 0.04);
  color: $main-green-dark;
}

.ai-custom-prompt button {
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
}

.ai-custom-prompt button:disabled {
  background: #e5eaf3;
  color: #aaa;
  cursor: not-allowed;
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
}

.triangle.expanded {
  transform: rotate(90deg);
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
}

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
</style>