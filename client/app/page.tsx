'use client'

import { useChatStore } from "@/stores/chat-store"
import { useAuth, useUser } from "@clerk/nextjs"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function WelcomePage() {
  const { addChat } = useChatStore()
  const router = useRouter()

  const { isLoaded, isSignedIn } = useAuth()

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.push('/sign-in')
    }
  }, [isLoaded, isSignedIn])

  const handleAddChat = () => {
    const newChat = addChat()
    router.push(`/chat/${newChat.id}`)
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-6xl md:text-8xl font-bold text-black mb-6 tracking-tight">Travel Genie</h1>
        <p className="text-xl md:text-2xl text-gray-600 mb-12 max-w-2xl mx-auto leading-relaxed">
          Your AI-powered travel companion that creates personalized itineraries and discovers hidden gems around the
          world
        </p>
        <button className="bg-black text-white px-12 py-4 text-lg font-medium hover:bg-gray-800 transition-colors duration-200 rounded-none border-2 border-black hover:border-gray-800" onClick={handleAddChat}>
          Start Chat
        </button>
      </div>
    </div>
  )
}

