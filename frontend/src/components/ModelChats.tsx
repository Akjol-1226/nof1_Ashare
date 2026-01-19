import { useState, useEffect } from 'react'
import { chatsWebSocket } from '../services/websocket'

interface ChatMessage {
  ai_name: string
  timestamp: string
  reasoning: string
}

export default function ModelChats() {
  const [chats, setChats] = useState<ChatMessage[]>([])

  useEffect(() => {
    // Connect to WebSocket
    chatsWebSocket.connect()

    // Listen for updates
    chatsWebSocket.onMessage((message) => {
      if (message.type === 'chats_update') {
        const data = message.data
        if (data && data.chats) {
          const allChats: ChatMessage[] = []

          data.chats.forEach((aiChat: any) => {
            if (aiChat.chats) {
              aiChat.chats.forEach((chat: any) => {
                allChats.push({
                  ai_name: aiChat.ai_name,
                  timestamp: new Date(chat.timestamp).toLocaleString('zh-CN', {
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                  }),
                  reasoning: chat.reasoning
                })
              })
            }
          })

          // Sort by timestamp descending
          allChats.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

          setChats(allChats)
        }
      }
    })

    return () => {
      chatsWebSocket.disconnect()
    }
  }, [])

  if (chats.length === 0) {
    return (
      <div className="border-2 border-border flex flex-col h-full">
        <div className="flex justify-between items-center p-4 border-b-2 border-border flex-shrink-0">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
            MODEL_CHATS
          </h2>
        </div>
        <div className="flex-1 flex justify-center items-center text-gray-500 text-xs">
          Waiting for model decisions...
        </div>
      </div>
    )
  }

  return (
    <div className="border-2 border-border flex flex-col h-full">
      <div className="flex justify-between items-center p-4 border-b-2 border-border flex-shrink-0">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
          AI Chats
        </h2>
      </div>
      <div className="space-y-3 p-4 overflow-y-auto flex-1">
        {chats.map((chat, index) => (
          <div key={index} className="flex gap-2">
            <div className="w-6 h-6 bg-gray-400 rounded-full flex items-center justify-center text-[10px] font-medium text-white flex-shrink-0">
              {chat.ai_name.charAt(0)}
            </div>
            <div className="text-xs flex-1">
              <p className="font-semibold">
                {chat.ai_name}{' '}
                <span className="text-gray-700 font-normal ml-2">
                  [{chat.timestamp}]
                </span>
              </p>
              <p className="text-gray-800 mt-1">{chat.reasoning}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
