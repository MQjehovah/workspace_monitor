import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket(url: string = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`) {
  const socket = ref<WebSocket | null>(null)
  const data = ref<any>(null)
  const connected = ref(false)
  
  const connect = () => {
    socket.value = new WebSocket(url)
    
    socket.value.onopen = () => {
      connected.value = true
      console.log('WebSocket connected')
    }
    
    socket.value.onmessage = (event) => {
      try {
        data.value = JSON.parse(event.data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
    
    socket.value.onclose = () => {
      connected.value = false
      console.log('WebSocket disconnected')
    }
    
    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }
  
  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
    }
  }
  
  onMounted(() => {
    connect()
  })
  
  onUnmounted(() => {
    disconnect()
  })
  
  return { data, connected, connect, disconnect }
}