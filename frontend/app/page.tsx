"use client";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "./context/AuthContext";
import { useRouter } from "next/navigation";

// Define the structure of a single message
interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const { token, logout } = useAuth();
  const router = useRouter();
  const chatEndRef = useRef<HTMLDivElement>(null); // Ref for auto-scrolling

  // State variables
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // --- THIS HOOK IS UPDATED ---
  useEffect(() => {
    const fetchHistory = async () => {
      if (token) {
        try {
          const response = await fetch("http://localhost:8000/conversations", {
            headers: {
              "Authorization": `Bearer ${token}`,
            },
          });
          if (!response.ok) {
            throw new Error("Could not fetch chat history.");
          }
          const history = await response.json();
          // The backend returns conversations, each with a 'messages' array.
          // We'll flatten this into a single list of messages for display.
          const formattedMessages = history.flatMap((conv: any) => conv.messages);
          setMessages(formattedMessages);
        } catch (error) {
          console.error(error);
          // Handle error, e.g., show a notification
        } finally {
          setIsCheckingAuth(false);
        }
      } else {
        router.push("/login");
      }
    };

    fetchHistory();
  }, [token, router]);


  // Auto-scroll to the latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ message: currentInput }),
      });

      if (!response.ok) {
        throw new Error("Failed to get a response from the AI.");
      }

      const data = await response.json();
      const aiMessage: Message = { role: "assistant", content: data.response };
      setMessages((prev) => [...prev, aiMessage]);

    } catch (error) {
      console.error(error);
      const errorMessage: Message = { role: "assistant", content: "Sorry, I couldn't connect to the AI. Please try again." };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  if (isCheckingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-900">
        <p className="text-white">Loading Your Conversations...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 p-4 flex justify-between items-center shadow-md">
        <h1 className="text-xl font-bold text-purple-400">WisePal AI</h1>
        <button
          onClick={handleLogout}
          className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition"
        >
          Logout
        </button>
      </header>

      <main className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-lg p-3 rounded-lg shadow ${msg.role === 'user' ? 'bg-purple-700' : 'bg-gray-700'}`}>
              <p className="text-white">{msg.content}</p>
            </div>
          </div>
        ))}
         {isLoading && (
            <div className="flex justify-start">
                <div className="max-w-lg p-3 rounded-lg bg-gray-700 shadow">
                    <p className="animate-pulse text-gray-300">Thinking...</p>
                </div>
            </div>
        )}
        {/* Empty div to mark the end of the chat for auto-scrolling */}
        <div ref={chatEndRef} />
      </main>

      <footer className="bg-gray-800 p-4">
        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask WisePal anything..."
            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none disabled:bg-gray-500 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      </footer>
    </div>
  );
}
