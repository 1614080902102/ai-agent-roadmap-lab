<script setup lang="ts">
import { ref, nextTick } from 'vue'

// 消息类型
interface Message {
  role: 'user' | 'assistant'
  content: string
}

// RAG 引用来源类型
interface Source {
  content: string
  file: string
}

// RAG 消息类型（带引用）
interface RagMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
}

// 模式切换
const mode = ref<'chat' | 'rag'>('chat')

// Chat 模式状态
const messages = ref<Message[]>([])
const history = ref<Message[]>([])

// RAG 模式状态
const ragMessages = ref<RagMessage[]>([])

// 共享状态
const input = ref('')
const loading = ref(false)
const error = ref('')

// 引用折叠状态：key = 消息索引，value = 是否展开
const expandedSources = ref<Record<number, boolean>>({})

function toggleSources(index: number) {
  expandedSources.value[index] = !expandedSources.value[index]
}

// 消息列表容器引用，用于自动滚到底部
const messagesContainer = ref<HTMLDivElement>()

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || loading.value) return

  if (mode.value === 'rag') {
    await sendRagMessage(text)
  } else {
    await sendChatMessage(text)
  }
}

// ── Chat 模式 ──────────────────────────────────────────────────────────────
async function sendChatMessage(text: string) {
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  error.value = ''

  // 提前占一个空的 assistant 气泡，后面往里追加内容（打字机效果的关键）
  messages.value.push({ role: 'assistant', content: '' })
  const assistantIdx = messages.value.length - 1
  await scrollToBottom()

  try {
    const res = await fetch('http://localhost:8000/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: history.value }),
    })

    if (!res.ok || !res.body) throw new Error('请求失败')

    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data:')) continue

        const dataStr = line.slice(5).trim()
        try {
          const data = JSON.parse(dataStr)

          if (data.delta) {
            messages.value[assistantIdx].content += data.delta
            await scrollToBottom()
          }

          if (data.done) {
            history.value = data.history
          }
        } catch { /* 忽略解析失败的行 */ }
      }
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// ── RAG 模式 ──────────────────────────────────────────────────────────────
async function sendRagMessage(text: string) {
  ragMessages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  error.value = ''
  await scrollToBottom()

  try {
    const res = await fetch('http://localhost:8000/rag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: text }),
    })

    if (!res.ok) throw new Error('请求失败')

    const data = await res.json()

    // 过滤掉 MiniMax 返回的 <think>...</think> 思考过程
    const cleanAnswer = (data.answer || '').replace(/<think>[\s\S]*?<\/think>\s*/g, '')

    ragMessages.value.push({
      role: 'assistant',
      content: cleanAnswer,
      sources: data.sources || [],
    })
    await scrollToBottom()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

// 按 Enter 发送，Shift+Enter 换行
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 从文件路径中提取文件名
function getFileName(path: string) {
  return path.split('/').pop() || path
}
</script>

<template>
  <div class="chat-container">
    <div class="header">
      <h2>AI Agent Demo</h2>
      <div class="mode-switch">
        <button
          :class="['mode-btn', { active: mode === 'chat' }]"
          @click="mode = 'chat'"
        >
          Chat
        </button>
        <button
          :class="['mode-btn', { active: mode === 'rag' }]"
          @click="mode = 'rag'"
        >
          RAG
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="messages" ref="messagesContainer">
      <!-- Chat 模式 -->
      <template v-if="mode === 'chat'">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          :class="['bubble', msg.role]"
        >
          {{ msg.content }}
        </div>
      </template>

      <!-- RAG 模式 -->
      <template v-else>
        <div v-for="(msg, i) in ragMessages" :key="i">
          <div :class="['bubble', msg.role]">
            {{ msg.content }}
          </div>

          <!-- 引用来源（折叠式） -->
          <div
            v-if="msg.sources && msg.sources.length > 0"
            class="sources-wrapper"
          >
            <button
              class="sources-toggle"
              @click="toggleSources(i)"
            >
              <span class="toggle-icon">{{ expandedSources[i] ? '▾' : '▸' }}</span>
              引用来源（{{ msg.sources.length }} 条）
            </button>

            <div v-if="expandedSources[i]" class="sources-list">
              <div
                v-for="(src, j) in msg.sources"
                :key="j"
                class="source-item"
              >
                <div class="source-file">{{ getFileName(src.file) }}</div>
                <div class="source-content">{{ src.content }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div v-if="loading" class="bubble assistant loading">AI 思考中...</div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <!-- 输入区 -->
    <div class="input-row">
      <textarea
        v-model="input"
        :placeholder="mode === 'rag' ? '输入问题，基于已上传文档回答' : '输入消息，Enter 发送，Shift+Enter 换行'"
        rows="2"
        @keydown="onKeydown"
      />
      <button :disabled="loading" @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<style scoped>
.chat-container {
  max-width: 700px;
  margin: 40px auto;
  padding: 0 16px;
  font-family: sans-serif;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.header h2 {
  margin: 0;
}

/* 模式切换按钮 */
.mode-switch {
  display: flex;
  gap: 0;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.mode-btn {
  padding: 6px 16px;
  border: none;
  background: #fff;
  color: #666;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.mode-btn.active {
  background: #4f46e5;
  color: white;
}

.mode-btn:not(.active):hover {
  background: #f3f4f6;
}

.messages {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  min-height: 400px;
  max-height: 60vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 12px;
  background: #fafafa;
}

.bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.bubble.user {
  align-self: flex-end;
  background: #4f46e5;
  color: white;
}

.bubble.assistant {
  align-self: flex-start;
  background: #e5e7eb;
  color: #111;
}

.bubble.loading {
  opacity: 0.5;
}

.error {
  color: red;
  font-size: 14px;
}

/* 引用来源样式 */
.sources-wrapper {
  max-width: 80%;
  margin-top: 4px;
}

.sources-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: none;
  background: none;
  color: #9ca3af;
  font-size: 12px;
  cursor: pointer;
  transition: color 0.2s;
}

.sources-toggle:hover {
  color: #6b7280;
}

.toggle-icon {
  font-size: 10px;
  width: 12px;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
  padding-left: 12px;
  border-left: 2px solid #e5e7eb;
}

.source-item {
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.4;
}

.source-file {
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 2px;
}

.source-content {
  white-space: pre-wrap;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.input-row {
  display: flex;
  gap: 8px;
}

textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  font-size: 14px;
}

button {
  padding: 0 20px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>