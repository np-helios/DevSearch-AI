import { useState, useRef, useEffect } from "react";
import axios from "axios";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const chatEndRef = useRef(null);

  const sendQuery = async () => {
    if (!query.trim()) return;

    const userMsg = { role: "user", text: query };
    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);

    try {
      const res = await axios.get("http://127.0.0.1:8000/ask", {
        params: { query, role: "employee" },
      });

      const botMsg = { role: "bot", text: res.data.answer };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Error fetching response 😢" },
      ]);
    }

    setLoading(false);
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-screen bg-[#343541] text-white">
      
      {/* Sidebar */}
      <div className="w-64 bg-[#202123] p-4 flex flex-col">
        <h1 className="text-lg font-bold mb-4">DevSearch AI</h1>
        <button className="bg-gray-700 px-3 py-2 rounded hover:bg-gray-600">
          + New Chat
        </button>
      </div>

      {/* Main Chat */}
      <div className="flex flex-col flex-1">

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`p-4 rounded-lg max-w-2xl ${
                msg.role === "user"
                  ? "bg-[#0b93f6] ml-auto"
                  : "bg-[#444654]"
              }`}
            >
              {msg.text}
            </div>
          ))}

          {loading && (
            <div className="bg-[#444654] p-4 rounded-lg w-fit">
              Typing...
            </div>
          )}

          <div ref={chatEndRef}></div>
        </div>

        {/* Input Box */}
        <div className="p-4 border-t border-gray-700 flex items-center">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Message DevSearch AI..."
            className="flex-1 p-3 rounded bg-[#40414f] outline-none"
            onKeyDown={(e) => e.key === "Enter" && sendQuery()}
          />
          <button
            onClick={sendQuery}
            className="ml-3 bg-green-600 px-5 py-2 rounded hover:bg-green-500"
          >
            Send
          </button>
        </div>

      </div>
    </div>
  );
}