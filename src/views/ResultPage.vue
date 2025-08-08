<template>
    <div class="ai-editor-layout">
        <!-- 编辑器区：两个编辑器上下排列 -->
        <div class="editor-panel">
            <div class="editors-double">
                <!-- 转写编辑器块，支持折叠/展开 -->
                <div class="editor-block" :class="{ 'transcribe-collapsed': transcribeCollapsed }">
                    <div class="editor-label transcribe-label" @click="onTranscribeLabelClick"
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
                    <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0;">
                        <div class="editor-label" style="font-weight: bold;">会议纪要</div>
                        <!-- 按钮组 -->
                        <div class="note-actions" style="display: flex; gap: 8px;">
                            <button class="preview-toggle-btn" @click="showMarkdownPreview = !showMarkdownPreview"
                                style="padding: 4px 10px; font-size: 14px; background-color: #95C11F; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                <i :class="showMarkdownPreview ? 'fa fa-pencil' : 'fa fa-eye'"
                                    style="margin-right: 4px;"></i>
                                {{ showMarkdownPreview ? '编辑' : '预览' }}
                            </button>
                        </div>
                    </div>
                    <div class="editor-content-fixed">
                        <div v-if="showMarkdownPreview" class="markdown-preview" v-html="markdownHtml"></div>
                        <editor-content v-else :editor="editor" />
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
            <!-- 底部操作按钮 -->
            <div class="flex justify-end gap-4 mt-8">
                <button @click="goBack" class="btn-secondary">
                    返回
                </button>
                <button @click="saveMeetingNote" class="btn-primary">
                    保存
                </button>
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
                            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                                <circle cx="32" cy="32" r="32" fill="#f0f7f0" />
                                <path d="M20 44v-2a8 8 0 0 1 8-8h8a8 8 0 0 1 8 8v2" stroke="#6da34d" stroke-width="2"
                                    stroke-linecap="round" />
                                <circle cx="24" cy="28" r="2" fill="#6da34d" />
                                <circle cx="40" cy="28" r="2" fill="#6da34d" />
                                <path d="M28 36c1.5 2 6.5 2 8 0" stroke="#6da34d" stroke-width="2"
                                    stroke-linecap="round" />
                            </svg>
                        </div>
                        <div class="ai-empty-text">
                            说点什么吧！让AI来帮助你理解会议
                        </div>
                    </div>
                </template>
                <div v-if="state.isLoading" class="hint purple-spinner" style="text-align:center;margin:8px 0;">
                    <span class="spinner"></span> AI 正在生成中……
                </div>
            </div>
            <div>
                <div v-if="selectedTextForPrompt" class="selected-bubble">
                    <span>选中内容：</span>
                    <div class="chat-bubble user">{{ selectedTextForPrompt }}</div>
                </div>
                <div class="ai-custom-prompt">
                    <input v-model="customPrompt" type="text" placeholder="请输入你的问题或需求"
                        @keyup.enter="sendCustomPrompt" />
                    <button @click="sendCustomPrompt" :disabled="!customPrompt || state.isLoading">发送</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
// 脚本部分保持不变（功能逻辑未修改）
import StarterKit from '@tiptap/starter-kit'
import { Editor, EditorContent } from '@tiptap/vue-3'
import OpenAI from 'openai'
import { Plugin } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'
import { defineComponent } from 'vue'
import { marked } from 'marked'

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
            transcribeCollapsed: true,
            showMarkdownPreview: true,
            meetingData: {
                transcribe: '',
                note: '',
            },
        }
    },

    computed: {
        isDisabled() {
            if (!this.editor) return true
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
            const rawContent = this.editor.getText()

            // 增强版Markdown转换逻辑，重点处理换行
            let markdownText = rawContent
                // 先将所有换行符统一处理
                .replace(/\r\n/g, '\n') // 处理Windows换行
                .replace(/\r/g, '\n')   // 处理Mac老式换行
                // 处理连续空行作为段落分隔
                .replace(/\n{2,}/g, '\n\n')
                // 处理单行换行（转换为<br>）
                .replace(/([^\n])\n([^\n])/g, '$1\n\n$2')
                // 处理代码块
                .replace(/```([\s\S]*?)```/g, (match, code) => {
                    return '```\n' + code.trim() + '\n```'
                })
                // 处理标题
                .replace(/(#{1,6} .+?)(?=\n|$)/g, '$1\n')
                // 处理列表
                .replace(/^(\s*)-\s/gm, '$1- ')
                .replace(/^(\s*)\*\s/gm, '$1* ')
                .replace(/^(\s*)\d+\.\s/gm, '$11. ')
                .trim()

            return marked.parse(markdownText)
        }
    },

    methods: {
        async fetchSummaryMd() {
            try {
                const response = await fetch('/summary.md')
                if (!response.ok) {
                    // 如果文件不存在，抛出错误让catch处理
                    if (response.status === 404) throw new Error('文件不存在')
                    throw new Error('获取summary.md失败')
                }
                let rawText = await response.text()
                const markdownContent = rawText
                    .replace(/\r\n/g, '<br>') // 处理 Windows 换行
                    .replace(/\r/g, '<br>')   // 处理老式 Mac 换行
                    .replace(/\n/g, '<br>')   // 处理 Unix 换行
                this.editor?.commands.setContent(markdownContent)
                this.isLoadingSummary = false // 加载成功，隐藏加载状态
                return true // 表示成功获取
            } catch (error) {
                console.log('当前未获取到summary.md，将继续尝试:', error.message)
                return false // 表示获取失败
            }
        },

        // 新增：定时检查summary.md的方法
        startSummaryCheck() {
            // 立即执行一次检查
            this.fetchSummaryMd().then(success => {
                if (success) {
                    // 如果成功获取，清除定时器
                    if (this.summaryCheckInterval) {
                        clearInterval(this.summaryCheckInterval)
                        this.summaryCheckInterval = null
                    }
                    return
                }

                // 如果第一次失败，设置定时器每5秒检查一次
                this.summaryCheckInterval = setInterval(async () => {
                    const success = await this.fetchSummaryMd()
                    if (success && this.summaryCheckInterval) {
                        clearInterval(this.summaryCheckInterval)
                        this.summaryCheckInterval = null
                    }
                }, 5000) // 5秒间隔
            })
        },

        async fetchCombinedOutput() {
            try {
                const response = await fetch('/combined_output.txt')
                if (!response.ok) {
                    if (response.status === 404) throw new Error('文件不存在')
                    throw new Error('获取转写失败')
                }
                let rawText = await response.text()
                const formattedText = rawText
                    .replace(/\r\n/g, '<br>') // 处理 Windows 换行
                    .replace(/\r/g, '<br>')   // 处理老式 Mac 换行
                    .replace(/\n/g, '<br>')   // 处理 Unix 换行
                this.transcribeEditor?.commands.setContent(formattedText)
                this.isLoadingSummary = false
                return true
            } catch (error) {
                console.log('当前未获取到转写，将继续尝试:', error.message)
                return false
            }
        },
        onTranscribeLabelClick() {
            this.transcribeCollapsed = !this.transcribeCollapsed
            if (!this.transcribeCollapsed) {
                this.fetchCombinedOutput()
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

        selectAllText() {
            if (!this.editor) return
            const { doc } = this.editor.state
            this.highlightRange = { from: 0, to: doc.content.size }
        },

        async runAiCommand(command) {
            if (!this.editor || !this.openai) return
            const { from, to } = this.editor.state.selection
            let selectedText = this.editor.state.doc.textBetween(from, to)
            let highlightFrom = from, highlightTo = to
            if (from === to) {
                selectedText = this.editor.getText().trim()
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
            const { from, to } = this.editor.state.selection
            let selectedText = this.editor.state.doc.textBetween(from, to)
            let highlightFrom = from, highlightTo = to
            if (from === to) {
                selectedText = this.editor.getText().trim()
            }
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

        async fetchMeetingData() {
            const res = await fetch('http://localhost:3001/api/meeting')
            const data = await res.json()
            this.transcribeEditor?.commands.setContent(data.transcribe || '')
            this.editor?.commands.setContent(data.note || '')
        },

        saveMeetingNote() {
            // 获取会议纪要内容（用markdown格式）
            const note = this.editor?.getText() || ''
            // 生成文件名，带时间戳，md后缀
            const filename = `会议纪要_${new Date().toLocaleDateString().replace(/\//g, '-')}_${new Date().toLocaleTimeString().replace(/:/g, '-')}.md`
            // 创建Blob并下载
            const blob = new Blob([note], { type: 'text/markdown;charset=utf-8' })
            if (window.navigator.msSaveOrOpenBlob) {
                window.navigator.msSaveOrOpenBlob(blob, filename)
            } else {
                const link = document.createElement('a')
                link.href = URL.createObjectURL(blob)
                link.download = filename
                document.body.appendChild(link)
                link.click()
                document.body.removeChild(link)
                URL.revokeObjectURL(link.href)
            }
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
        this.startSummaryCheck()
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
          # 接口学习  

**时间**：2025-08-04 08:01  
**主讲人**：未设置  
**参会人**：未设置  
**记录人**：未设置  

## 一、分享概览  
- **核心内容**：本次会议围绕接口设计与开发展开，涵盖接口功能划分、前后端交互流程、开发工具推荐、AI辅助编程的局限性及并发调用优化等内容。  
- **关键结论**：接口设计需功能分离优先，开发推荐使用\`fastAPI\`和\`Postman\`工具，AI辅助编程需人工验证，并发调用需注意模型选择和token限制。  

</p >
      `,
            parseOptions: {
                preserveWhitespace: true,
            }
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
        // 组件卸载时清除定时器
        if (this.summaryCheckInterval) {
            clearInterval(this.summaryCheckInterval)
        }
    },
})
</script>

<style lang="scss">
// 基础变量调整为低饱和色调，提升简洁感
$primary: #6da34d; // 主色调：低饱和绿色
$primary-light: #f0f7f0; // 浅绿背景
$primary-dark: #4a7d36; // 深绿文字
$primary-accent: #8dc075; // 强调色
$gray-light: #f8f9fa; // 浅灰背景
$gray-mid: #e9ecef; // 边框/分割线
$text-primary: #333333; // 主要文字
$text-secondary: #6c757d; // 次要文字
$shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.05); // 轻量阴影
$shadow-md: 0 4px 12px rgba(0, 0, 0, 0.07); // 中等阴影
$radius-sm: 6px;
$radius-md: 10px;
$radius-lg: 14px;
$transition: all 0.25s ease; // 统一过渡动画

.ai-editor-layout {
    display: flex;
    background: $primary-light;
    height: 100vh;
    width: 100%;
    font-family: "Inter", "PingFang SC", "Microsoft YaHei", Arial, sans-serif; // 现代无衬线字体
    min-height: 0;
    overflow: hidden;
    padding: 16px; // 整体外间距
    box-sizing: border-box;
}

.editor-panel {
    flex: 2 1 0;
    min-width: 0;
    background: #fff;
    border-radius: $radius-lg;
    box-shadow: $shadow-md;
    padding: 24px; // 内边距优化
    margin: 0 12px 0 0; // 间距调整
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;
}

.editors-double {
    display: flex;
    flex-direction: column;
    gap: 20px; // 编辑器间距优化
    flex: 1 1 0;
}

.editor-block {
    flex: 1 1 0;
    display: flex;
    flex-direction: column;
    background: $gray-light;
    border-radius: $radius-md;
    box-shadow: $shadow-sm;
    padding: 16px; // 内边距统一
    transition: flex 0.3s, max-height 0.3s, box-shadow 0.2s; // 增加阴影过渡

    &:hover {
        box-shadow: $shadow-md; // 悬浮增强阴影
    }

    &.transcribe-collapsed {
        flex: 0 0 auto;
        max-height: 36px;
        padding: 0 16px; // 折叠状态内边距
        background: transparent;
        box-shadow: none;
        border-radius: $radius-md $radius-md 0 0;
    }

    &.main-expanded {
        flex: 1 1 auto;
    }
}

.editor-label {
    font-weight: 600;
    font-size: 16px;
    color: $primary-dark;
    margin-bottom: 12px;
    letter-spacing: 0.3px; // 字间距优化
    display: flex;
    align-items: center;
}

.editor-content-fixed {
    flex: 1 1 0;
    min-height: 0;
    height: 100%;
    width: 100%;
    overflow-y: auto;
    border-radius: $radius-sm;
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
        padding: 8px 0; // 编辑器内边距
        overflow-y: auto;
        display: block;
        line-height: 1.6; // 行高优化
        font-size: 15px;
        color: $text-primary;
    }
}

// 功能按钮组优化
.button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 10px; // 按钮间距
    margin: 16px 0 0 0;

    button {
        background: $primary;
        color: #fff;
        border: none;
        border-radius: $radius-sm;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: $transition;
        box-shadow: $shadow-sm;
        display: inline-flex;
        align-items: center;
        justify-content: center;

        &:hover {
            background: $primary-dark;
            transform: translateY(-1px); // 轻微上浮效果
            box-shadow: 0 3px 9px rgba(109, 163, 77, 0.2);
        }

        &:active {
            transform: translateY(0); // 点击回落
        }

        &:disabled {
            background: $gray-mid;
            color: #aaa;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
    }
}

// 纪要操作按钮
.note-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px; // 按钮间距
    margin-top: 16px;
    margin-bottom: 0;

    button {
        display: flex;
        align-items: center;
        gap: 6px; // 图标文字间距
        padding: 9px 20px; // 按钮尺寸优化
        border-radius: $radius-sm;
        border: none;
        font-size: 14px;
        font-weight: 500;
        background: $primary;
        color: #fff;
        box-shadow: $shadow-sm;
        cursor: pointer;
        transition: $transition;

        i {
            font-size: 16px; // 图标大小
        }

        &:hover {
            background: $primary-dark;
            transform: translateY(-1px);
            box-shadow: 0 3px 9px rgba(109, 163, 77, 0.2);
        }

        &:active {
            transform: translateY(0);
        }

        &:disabled {
            background: $gray-mid;
            color: #aaa;
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }
    }
}

// 提示文本样式
.hint {
    margin-bottom: 10px;
    font-size: 14px;
    color: $primary-dark;
    padding: 6px 0; // 内边距优化
    line-height: 1.5;

    &.error {
        color: #d93025;
        background: #fff0f0;
        border-radius: $radius-sm;
        padding: 8px 12px; // 错误提示内边距
        margin-top: 8px;
    }

    &.purple-spinner {
        font-weight: 500;
        padding: 12px 0; // 加载提示 padding
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;

        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(109, 163, 77, 0.3);
            border-radius: 50%;
            border-top-color: $primary;
            animation: spin 1s ease-in-out infinite;
        }
    }
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.editor-placeholder {
    color: #999;
    padding: 20px;
    text-align: center;
    position: absolute;
    width: 100%;
    pointer-events: none;
    z-index: 1;
    font-size: 15px;
    background: $gray-light;
    border-radius: $radius-sm;
    box-sizing: border-box;
}

// 右侧AI结果面板
.ai-result-panel {
    flex: 1 1 0;
    min-width: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px; // 内部间距
    background: #fff;
    border-radius: $radius-lg;
    box-shadow: $shadow-md;
    padding: 24px; // 内边距
    margin: 0 0 0 12px; // 间距调整
    position: relative;
    min-height: 0;
    overflow: hidden;
    box-sizing: border-box;
}

.ai-result-title {
    font-weight: 600;
    font-size: 18px;
    margin-bottom: 4px; // 标题下方间距
    color: $primary-dark;
    letter-spacing: 0.3px;
    padding-bottom: 8px;
    border-bottom: 1px solid $gray-mid; // 标题下分割线
}

.ai-chat-history-scroll {
    flex: 1 1 0;
    min-height: 0;
    height: 100%;
    overflow-y: auto;
    padding: 8px 4px; // 内边距优化
    margin-bottom: 8px;
    scrollbar-width: thin;
    scrollbar-color: $primary $primary-light;
    background: $gray-light;
    border-radius: $radius-md;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.03); // 内阴影增强质感

    &::-webkit-scrollbar {
        width: 6px; // 滚动条宽度
    }

    &::-webkit-scrollbar-thumb {
        background: $primary;
        border-radius: 3px; // 滚动条圆角
    }

    &::-webkit-scrollbar-track {
        background: $primary-light;
        border-radius: 3px;
    }
}

// 聊天记录样式
.chat-item {
    margin-bottom: 14px; // 消息间距
    padding: 0 8px; // 内边距
}

.chat-row {
    display: flex;
    justify-content: flex-start;
    align-items: flex-end;
    gap: 12px; // 间距优化
}

.chat-user-side {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    max-width: 75%; // 宽度调整
    margin-left: auto;
}

.chat-ai-side {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    max-width: 75%; // 宽度调整
}

.chat-bubble {
    position: relative;
    padding: 10px 14px; // 内边距优化
    border-radius: 16px; // 气泡圆角
    margin-bottom: 4px;
    max-width: 100%;
    word-break: break-word; // 文字换行优化
    font-size: 14px;
    line-height: 1.6; // 行高优化
    box-shadow: $shadow-sm;

    &.ai {
        background: #fff;
        color: $text-primary;
        border-bottom-left-radius: 4px; // 左侧气泡左下角圆角
        border-top-left-radius: 4px;
        margin-left: 4px;
        align-self: flex-start;

        &::before {
            content: "";
            position: absolute;
            left: -6px;
            top: 12px;
            border-width: 6px 8px 6px 0;
            border-style: solid;
            border-color: transparent #fff transparent transparent;
        }
    }

    &.user {
        background: $primary;
        color: #fff;
        border-bottom-right-radius: 4px; // 右侧气泡右下角圆角
        border-top-right-radius: 4px;
        margin-right: 4px;
        align-self: flex-end;

        &::before {
            content: "";
            position: absolute;
            right: -6px;
            top: 12px;
            border-width: 6px 0 6px 8px;
            border-style: solid;
            border-color: transparent transparent transparent $primary;
        }
    }
}

// 聊天操作按钮
.chat-actions {
    display: flex;
    gap: 6px; // 按钮间距
    margin-top: 2px;

    &.left {
        justify-content: flex-start;
        padding-left: 24px; // 左对齐偏移
    }

    button {
        background: $primary-light;
        color: $primary-dark;
        border: none;
        border-radius: 4px; // 按钮圆角
        padding: 3px 10px; // 按钮尺寸
        font-size: 12px; // 字体大小
        cursor: pointer;
        box-shadow: $shadow-sm;
        transition: $transition;

        &:hover {
            background: $primary;
            color: #fff;
        }

        &:disabled {
            background: $gray-mid;
            color: #aaa;
            cursor: not-allowed;
        }
    }
}

// 选中内容气泡
.selected-bubble {
    margin-bottom: 10px;
    font-size: 13px;
    color: $text-secondary;
    display: flex;
    align-items: flex-start; // 对齐优化
    gap: 6px;

    .chat-bubble.user {
        display: inline-block;
        margin-left: 0;
        background: $primary-light;
        padding: 6px 12px;
        border-radius: 10px;
        max-width: 80%;
        word-break: break-all;
        font-size: 14px;
        box-shadow: $shadow-sm;
        color: $primary-dark;
        max-height: 4.5em;
        overflow-y: auto;
    }
}

// 自定义提示输入框
.ai-custom-prompt {
    display: flex;
    gap: 8px; // 间距优化
    margin-bottom: 4px;

    input {
        flex: 1;
        padding: 10px 14px; // 输入框内边距
        border-radius: $radius-sm;
        border: 1px solid $primary-light;
        font-size: 14px;
        background: $gray-light;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05); // 内阴影
        color: $text-primary;
        transition: $transition;

        &:focus {
            outline: none;
            border-color: $primary; // 聚焦边框色
            box-shadow: 0 0 0 2px rgba(109, 163, 77, 0.2); // 聚焦发光效果
        }

        &::placeholder {
            color: #999; // 占位符颜色
        }
    }

    button {
        padding: 0 18px; // 按钮尺寸
        border-radius: $radius-sm;
        background: $primary;
        color: #fff;
        border: none;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        box-shadow: $shadow-sm;
        transition: $transition;

        &:hover {
            background: $primary-dark;
            transform: translateY(-1px);
        }

        &:active {
            transform: translateY(0);
        }

        &:disabled {
            background: $gray-mid;
            color: #aaa;
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }
    }
}

// 折叠三角图标
.transcribe-label {
    display: flex;
    align-items: center;
    gap: 6px;
}

.triangle {
    display: inline-block;
    transition: transform 0.2s ease; // 平滑旋转
    font-size: 14px;
    color: $primary;

    &.expanded {
        transform: rotate(90deg);
    }
}

// 折叠过渡动画
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.2s ease, transform 0.2s ease; // 增加位移动画
    transform: translateY(0);
    opacity: 1;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(-8px); // 入场/离场位移
}

// 空状态样式
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
        margin-bottom: 16px; // 图标间距
        opacity: 0.8; // 轻微透明
    }

    .ai-empty-text {
        font-size: 16px;
        color: $primary;
        font-weight: 500;
        letter-spacing: 0.3px;
        text-align: center;
    }
}

// Markdown预览样式优化
.markdown-preview {
    margin-top: 0;
    padding: 12px 0; // 内边距
    background: transparent;
    border-radius: 0;
    border: none;
    font-size: 15px;
    color: $text-primary;
    height: 100%;
    max-height: none;
    overflow: auto;
    width: 100%;
    box-shadow: none;
    line-height: 1.7; // 行高优化

    /* Markdown基础样式优化 */
    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        font-weight: 600;
        margin: 1.2em 0 0.6em 0; // 标题间距
        color: $primary-dark;
        line-height: 1.4;
    }

    h1 {
        font-size: 1.8em;
        border-bottom: 2px solid $primary-light;
        padding-bottom: 0.3em;
        margin-top: 0.5em;
    }

    h2 {
        font-size: 1.5em;
        border-bottom: 1px solid $primary-light;
        padding-bottom: 0.2em;
    }

    h3 {
        font-size: 1.3em;
        color: $primary;
    }

    h4,
    h5,
    h6 {
        font-size: 1.1em;
    }

    p {
        margin: 0.8em 0; // 段落间距
        line-height: 1.7;
    }

    ul,
    ol {
        margin: 0.8em 0;
        padding-left: 1.8em; // 列表缩进
    }

    li {
        margin: 0.4em 0;
        line-height: 1.6;
    }

    // 嵌套列表样式
    ul ul,
    ol ol,
    ul ol,
    ol ul {
        margin-left: 0.5em;
        padding-left: 1em;
    }

    table {
        border-collapse: collapse;
        margin: 1.2em 0;
        width: 100%;
        font-size: 14px;
        background: #fff;
        border-radius: $radius-sm;
        overflow: hidden; // 表格圆角
    }

    th,
    td {
        border: 1px solid $gray-mid;
        padding: 8px 12px; // 单元格内边距
        text-align: left;
    }

    th {
        background: $primary-light;
        color: $primary-dark;
        font-weight: 600;
    }

    code {
        background: $primary-light;
        border-radius: 4px;
        padding: 0.2em 0.4em;
        font-size: 13px;
        color: $primary-dark;
        font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
    }

    pre code {
        display: block;
        padding: 12px;
        background: $gray-light;
        border-radius: $radius-sm;
        font-size: 13px;
        overflow-x: auto;
        border: 1px solid $gray-mid;
    }

    blockquote {
        border-left: 3px solid $primary;
        background: $primary-light;
        margin: 1em 0;
        padding: 0.6em 1em;
        color: $text-secondary;
        border-radius: 0 $radius-sm $radius-sm 0; // 引用圆角
    }

    strong {
        font-weight: 600;
        color: $primary-dark;
    }

    em {
        font-style: italic;
        color: $primary-dark;
    }

    hr {
        border: none;
        border-top: 1px solid $gray-mid;
        margin: 1.5em 0;
    }
}

// 选中高亮样式
.ai-highlight {
    background: rgba(141, 192, 117, 0.2) !important; // 淡绿色高亮
    border-radius: 2px;
    padding: 0 2px;
}

.summary-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.9);
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #6da34d;
    font-weight: 500;

    .spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(109, 163, 77, 0.3);
        border-radius: 50%;
        border-top-color: #6da34d;
        animation: spin 1s ease-in-out infinite;
    }
}
</style>
