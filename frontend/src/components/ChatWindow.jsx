import { useEffect, useRef } from "react";

import "./ChatWindow.css";
import ChatInput from "./ChatInput";

function ChatWindow({
  selectedSession,
  messages,
  question,
  setQuestion,
  handleSendMessage,
  loading,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2 className="chat-title">
          {selectedSession?.title || "No Session Selected"}
        </h2>

        <div className="header-actions">
          <button className="doc-btn">
            📄 0 Documents
          </button>

          <button className="upload-btn">
            + Upload
          </button>
        </div>
      </div>

      {!selectedSession ? (
        <div className="empty-state">
          <div className="empty-content">
            <h1>🧠 DocuMind</h1>
            <p>Create or select a chat to get started.</p>
          </div>
        </div>
      ) : messages.length === 0 && !loading ? (
        <div className="empty-state">
          <div className="empty-content">
            <p>No messages yet. Ask your first question.</p>
          </div>
        </div>
      ) : (
        <div className="messages-area">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-row ${
                message.role === "user"
                  ? "user-row"
                  : "assistant-row"
              }`}
            >
              <div
                className={`message-bubble ${
                  message.role === "user"
                    ? "user-bubble"
                    : "assistant-bubble"
                }`}
              >
                <strong>
                  {message.role === "user"
                    ? "👤 You"
                    : "🤖 Assistant"}
                </strong>
                <p className="message-content">
                  {message.content}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant-row">
              <div className="message-bubble assistant-bubble">
                <strong>
                  ðŸ¤– Assistant
                </strong>
                <p className="message-content">
                  Generating answer...
                </p>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}

      {selectedSession && (
        <ChatInput
          value={question}
          onChange={setQuestion}
          onSend={handleSendMessage}
          loading={loading}
        />
      )}
    </div>
  );
}

export default ChatWindow;
