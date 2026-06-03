import "./ChatInput.css";

function ChatInput() {
  return (
    <div className="chat-input-container">
      <input
        className="chat-input"
        type="text"
        placeholder="Ask about your documents..."
      />
    </div>
  );
}

export default ChatInput;