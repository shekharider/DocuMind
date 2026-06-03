import "./ChatWindow.css";
import ChatInput from "./ChatInput";

function ChatWindow() {
  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2 className="chat-title">
          Machine Learning Notes
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

      <div className="empty-state">
        <div className="empty-content">
          <h1>🧠 DocuMind</h1>

          <p>
            Chat with your PDFs
          </p>

          <p>
            Upload documents and ask
            questions using AI-powered search.
          </p>
        </div>
      </div>

      <ChatInput />
    </div>
  );
}

export default ChatWindow;