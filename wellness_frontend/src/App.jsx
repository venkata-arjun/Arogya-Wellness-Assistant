import { useState, useRef, useEffect } from "react";
import { sendWellnessMessage } from "./api/wellness";
import {
  Send,
  Bot,
  Loader2,
  Copy,
  Check,
  Sun,
  Moon,
  ArrowRightCircle,
} from "lucide-react";
import Logo from "./assets/logo.png";
import BlackLogo from "./assets/black-logo.png";

function App() {
  // -----------------------
  // NEW: Home screen toggle
  // -----------------------
  const [showHome, setShowHome] = useState(true);

  // -----------------------
  // USER ID PER BROWSER
  // -----------------------
  const [userId, setUserId] = useState("");

  useEffect(() => {
    let id = localStorage.getItem("wellness_user_id");

    if (!id) {
      const randomPart = Math.random().toString(36).substring(2, 10);
      id = `user_${randomPart}`;
      localStorage.setItem("wellness_user_id", id);
    }

    setUserId(id);
  }, []);

  // -----------------------
  // MAIN STATES
  // -----------------------
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  const chatRef = useRef(null);
  const inputRef = useRef(null);

  // -----------------------
  // RESTORE CHAT IF EXISTS
  // -----------------------
  useEffect(() => {
    const savedChat = localStorage.getItem("wellness_chat_history");
    if (savedChat) setChat(JSON.parse(savedChat));
  }, []);

  useEffect(() => {
    localStorage.setItem("wellness_chat_history", JSON.stringify(chat));
  }, [chat]);

  useEffect(() => {
    if (chatRef.current)
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [chat]);

  useEffect(() => inputRef.current?.focus(), []);

  // -----------------------
  // FORMAT BOT OUTPUT
  // -----------------------
  const formatBotMessage = (output) => {
    let text = "";

    if (output.symptom) text += `**Symptom**\n${output.symptom}\n\n`;
    if (output.observations?.length)
      text += `**Observations**\n${output.observations
        .map((o) => `• ${o}`)
        .join("\n")}\n\n`;
    if (output.diet_guidance?.length)
      text += `**Diet Guidance**\n${output.diet_guidance
        .map((o) => `• ${o}`)
        .join("\n")}\n\n`;
    if (output.lifestyle_advice?.length)
      text += `**Lifestyle Advice**\n${output.lifestyle_advice
        .map((o) => `• ${o}`)
        .join("\n")}\n\n`;
    if (output.physical_activity_suggestions?.length)
      text += `**Physical Activity**\n${output.physical_activity_suggestions
        .map((o) => `• ${o}`)
        .join("\n")}\n\n`;
    if (output.conclusion) text += `**Conclusion**\n${output.conclusion}`;

    return text.trim();
  };

  const copyMessage = (id, output) => {
    navigator.clipboard.writeText(
      formatBotMessage(output).replace(/\*\*(.*?)\*\*/g, "$1")
    );
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1200);
  };

  // -----------------------
  // SEND MESSAGE
  // -----------------------
  const handleSend = async () => {
    const trimmed = message.trim();
    if (!trimmed || isLoading) return;

    const time = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    setChat((prev) => [
      ...prev,
      { id: Date.now(), sender: "user", text: trimmed, time },
    ]);
    setMessage("");
    setIsLoading(true);

    try {
      const data = await sendWellnessMessage(userId, trimmed);
      setChat((prev) => [
        ...prev,
        { id: Date.now() + 1, sender: "bot", output: data.final_output, time },
      ]);
    } catch {
      setChat((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: "bot",
          time,
          output: {
            symptom: "Connection Error",
            conclusion: "Unable to process your request. Try again.",
          },
        },
      ]);
    }

    setIsLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // -----------------------------------------------------
  // HOME SCREEN (NEW)
  // -----------------------------------------------------
  if (showHome) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-white dark:bg-black dark:text-white px-6 text-center">
        <img
          src={darkMode ? BlackLogo : Logo}
          alt="Arogya Logo"
          className="w-64 h-64 sm:w-80 sm:h-80 mb-0 object-contain transition-transform duration-300 hover:scale-110"
        />

        <h1 className="text-2xl sm:text-4xl font-bold mb-3">
          Arogya Wellness Assistant
        </h1>

        <p className="text-gray-600 dark:text-gray-400 max-w-md mb-8 text-sm sm:text-base">
          Your AI-powered wellness companion. Understand symptoms, receive
          structured guidance, and build healthier habits.
        </p>

        <button
          onClick={() => setShowHome(false)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl text-base font-semibold"
        >
          Start Chat
          <ArrowRightCircle size={20} />
        </button>
      </div>
    );
  }

  // -----------------------------------------------------
  // CHAT UI (UNCHANGED EXCEPT RESPONSIVE FIXES)
  // -----------------------------------------------------
  return (
    <div className={darkMode ? "dark min-h-screen" : "min-h-screen"}>
      <div className="w-full h-screen flex flex-col bg-white dark:bg-black dark:text-white">
        {/* HEADER */}
        <header className="px-3 py-3 sm:px-4 border-b bg-white dark:bg-zinc-900 dark:border-zinc-800 flex justify-between items-center shadow-sm flex-shrink-0">
          <h1 className="text-lg sm:text-xl font-semibold">
            Arogya Wellness Assistant
          </h1>

          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-full bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700"
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </header>

        {/* CHAT AREA */}
        <div
          ref={chatRef}
          className="flex-1 overflow-y-auto px-3 sm:px-6 py-4 sm:py-6"
        >
          <div className="space-y-4 max-w-3xl mx-auto">
            {chat.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-gray-600 dark:text-gray-400 py-10 px-4">
                <img
                  src={darkMode ? BlackLogo : Logo}
                  alt="Arogya Logo"
                  className="w-40 h-40 sm:w-48 sm:h-48 mb-4 object-contain"
                />
                <p className="text-xl sm:text-2xl font-semibold mb-2 text-gray-800 dark:text-white">
                  Welcome to Arogya!
                </p>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                  Share any wellness concerns or health questions you have.
                </p>
              </div>
            )}

            {chat.map((msg) => (
              <div key={msg.id}>
                {msg.sender === "user" ? (
                  <div className="flex justify-end">
                    <div className="max-w-[90%] sm:max-w-[75%] md:max-w-[65%]">
                      <div className="bg-blue-600 dark:bg-zinc-800 text-white px-3 py-2 sm:px-4 sm:py-3 rounded-xl shadow whitespace-pre-line text-sm sm:text-base">
                        {msg.text}
                      </div>
                      <p className="text-[10px] text-gray-400 mt-1 text-right">
                        {msg.time}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start space-x-3">
                    <div className="hidden sm:flex w-9 h-9 bg-gray-200 dark:bg-zinc-800 rounded-full items-center justify-center">
                      <Bot
                        size={18}
                        className="text-gray-700 dark:text-gray-400"
                      />
                    </div>

                    <div className="max-w-[90%] sm:max-w-[75%] md:max-w-[65%] w-full">
                      <div className="relative bg-gray-100 dark:bg-zinc-900 text-gray-900 dark:text-white px-3 py-3 sm:px-4 sm:py-4 rounded-xl shadow whitespace-pre-line text-sm sm:text-base leading-relaxed">
                        <div
                          dangerouslySetInnerHTML={{
                            __html: formatBotMessage(msg.output).replace(
                              /\*\*(.*?)\*\*/g,
                              "<strong>$1</strong>"
                            ),
                          }}
                        />

                        <button
                          onClick={() => copyMessage(msg.id, msg.output)}
                          className="absolute top-2 right-2 p-1 rounded bg-gray-200 dark:bg-zinc-800 hover:bg-gray-300 dark:hover:bg-zinc-700"
                        >
                          {copiedId === msg.id ? (
                            <Check size={16} className="text-green-500" />
                          ) : (
                            <Copy
                              size={16}
                              className="text-gray-600 dark:text-gray-400"
                            />
                          )}
                        </button>
                      </div>
                      <p className="text-[10px] text-gray-400 mt-1">
                        {msg.time}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 text-sm">
                <Loader2 className="animate-spin text-blue-500" />
                <span>Thinking...</span>
              </div>
            )}
          </div>
        </div>

        {/* INPUT BAR */}
        <footer className="p-2 sm:p-3 border-t bg-white dark:bg-zinc-900 dark:border-zinc-800 flex-shrink-0">
          <div className="max-w-3xl mx-auto flex gap-2 sm:gap-3">
            <textarea
              ref={inputRef}
              rows={1}
              placeholder="Type your message..."
              disabled={isLoading}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 border border-gray-300 dark:border-zinc-700 dark:bg-zinc-900 dark:text-white rounded-xl p-2 sm:p-3 resize-none outline-none focus:ring-2 focus:ring-blue-500 text-sm sm:text-base"
            />

            <button
              onClick={handleSend}
              disabled={!message.trim() || isLoading}
              className={`w-9 h-9 sm:w-11 sm:h-11 flex items-center justify-center rounded-xl text-white ${
                !message.trim() || isLoading
                  ? "bg-gray-300 dark:bg-zinc-800"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              {isLoading ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>

          <p className="text-center text-gray-400 dark:text-gray-500 text-[10px] sm:text-xs mt-1 sm:mt-2">
            Arogya Assistant may make mistakes. Verify important information.
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
