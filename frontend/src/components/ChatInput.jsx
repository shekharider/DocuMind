import "./ChatInput.css";

function ChatInput({
  value,
  onChange,
  onSend,
  loading,
}) {
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      onSend();
    }
  };

  return (
    <div className="chat-input-container">
      <input
        className="chat-input"
        type="text"
        placeholder="Ask about your documents..."
        value={value}
        onChange={(e) =>
          onChange(e.target.value)
        }
        onKeyDown={handleKeyDown}
        disabled={loading}
      />

      <button
        className="chat-send-btn"
        onClick={onSend}
        disabled={loading}
      >
        {loading ? "Loading..." : "Send"}
      </button>
    </div>
  );
}

export default ChatInput;
