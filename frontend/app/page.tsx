"use client";
import { useState, useEffect, FormEvent, useRef } from "react";
import { useAuth } from "./context/AuthContext";
import { useRouter } from "next/navigation";


interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const { token, logout } = useAuth();
  const router = useRouter();

  
  const [input, setInput] = useState("");
  
  const [messages, setMessages] = useState<Message[]>([]);
  
  const [isLoading, setIsLoading] = useState(false);
  
  const [error, setError] = useState("");

  const chatEndRef = useRef<HTMLDivElement>(null);

 
  useEffect(() => {
    if (!token) {
      router.push("/login");
    } else {
      
      const fetchHistory = async () => {
        try {
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/conversations`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });
          if (!res.ok) {
            throw new Error("Failed to fetch history");
          }
          const data = await res.json();
          
          const allMessages = data.flatMap((convo: any) => convo.messages);
          setMessages(allMessages);
        } catch (err) {
          console.error(err);
          setError("Could not load chat history.");
        }
      };
      fetchHistory();
    }
  }, [token, router]);

  
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


  
  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok.");
      }

      const data = await response.json();
      const aiMessage: Message = { role: "assistant", content: data.response };
      setMessages((prev) => [...prev, aiMessage]);

    } catch (err) {
      setError("Sorry, I'm having trouble connecting. Please try again later.");
    } finally {
      setIsLoading(false);
    }
  };

  
  if (!token) {
    return null;
  }

  return (
    <div className="flex h-screen flex-col bg-gray-900 text-white">
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
          <div
            key={index}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-lg rounded-lg px-4 py-2 ${
                msg.role === "user"
                  ? "bg-purple-600"
                  : "bg-gray-700"
              }`}
            >
              <p>{msg.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-lg rounded-lg px-4 py-2 bg-gray-700">
              <p className="animate-pulse">Thinking...</p>
            </div>
          </div>
        )}

        {error && (
           <div className="flex justify-start">
            <div className="max-w-lg rounded-lg px-4 py-2 bg-red-800 text-red-200">
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* This empty div is the target for our auto-scrolling */}
        <div ref={chatEndRef} />
      </main>

      <footer className="p-4 bg-gray-800">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask WisePal anything..."
            className="flex-1 p-2 bg-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded disabled:bg-gray-500 transition"
            disabled={isLoading}
          >
            Send
          </button>
        </form>
      </footer>
    </div>
  );
}