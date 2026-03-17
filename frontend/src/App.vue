<script setup lang="ts">
import { ref } from 'vue'

// 消息类型
interface Message {
  role: 'user' | 'assistant'
  content: string
}

// 响应式状态（类比 React 的 useState）
const messages = ref<Message[]>([])  // 展示用的消息列表
const history = ref<Message[]>([])   // 传给后端的对话历史
const input = ref('')
const loading = ref(false)
const error = ref('')

async function sendMessage() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  error.value = ''

  // 提前占一个空的 assistant 气泡，后面往里追加内容（打字机效果的关键）
  messages.value.push({ role: 'assistant', content: '' })
  const assistantIdx = messages.value.length - 1

  try {
    const res = await fetch('http://localhost:8000/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: history.value }),
    })

    if (!res.ok || !res.body) throw new Error('请求失败')

    // ReadableStream：把响应体当成一个"水管"，一块一块读
    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // 一次 read() 可能包含多行 SSE，按 \n\n 切割
      const chunk = decoder.decode(value)
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data:')) continue

        const dataStr = line.slice(5).trim()
        try {
          const data = JSON.parse(dataStr)

          if (data.delta) {
            // 每收到一段增量，追加到 assistant 气泡里
            messages.value[assistantIdx].content += data.delta
          }

          if (data.done) {
            // 流结束，更新 history 供下一轮对话使用
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

// 按 Enter 发送，Shift+Enter 换行
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="chat-container">
    <h2>AI Agent Demo</h2>

    <!-- 消息列表 -->
    <div class="messages">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['bubble', msg.role]"
      >
        {{ msg.content }}
      </div>
      <div v-if="loading" class="bubble assistant loading">AI 思考中...</div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <!-- 输入区 -->
    <div class="input-row">
      <textarea
        v-model="input"
        placeholder="输入消息，Enter 发送，Shift+Enter 换行"
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
