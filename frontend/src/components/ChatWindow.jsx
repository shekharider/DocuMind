import { useEffect, useRef, useState } from "react";

import "./ChatWindow.css";
import ChatInput from "./ChatInput";

function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false);
  const hasSources =
    message.role === "assistant" &&
    message.sources &&
    message.sources.length > 0;

  return (
    <div
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
            ? "You"
            : "Assistant"}
        </strong>
        <p className="message-content">
          {message.content}
        </p>

        {hasSources && (
          <>
            <button
              className="sources-toggle"
              onClick={() =>
                setShowSources(!showSources)
              }
            >
              Sources ({message.sources.length})
            </button>

            <div
              className={`sources-panel ${
                showSources ? "open" : ""
              }`}
            >
              {message.sources.map((source) => (
                <div
                  key={source}
                  className="source-item"
                >
                  Chunk #{source}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ChatWindow({
  selectedSession,
  messages,
  question,
  setQuestion,
  handleSendMessage,
  loading,
  documents,
  showDocuments,
  setShowDocuments,
  handleUpload,
  uploading,
  deleteDocumentId,
  deletingDocument,
  onDeleteDocument,
}) {

  const bottomRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];

    if (file) {
      handleUpload(file);
    }

    e.target.value = "";
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2 className="chat-title">
          {selectedSession?.title || "No Session Selected"}
        </h2>

        <div className="header-actions">
          <button
            className="doc-btn"
            onClick={() =>
              setShowDocuments(!showDocuments)
            }
            disabled={!selectedSession}
          >
            📄 {documents.length} Documents
          </button>

          <button
            className="upload-btn"
            onClick={() =>
              fileInputRef.current?.click()
            }
            disabled={!selectedSession || uploading}
          >
            {uploading ? "Uploading..." : "+ Upload"}
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            className="file-input"
            onChange={handleFileChange}
          />
        </div>

        {showDocuments && selectedSession && (
          <div className="documents-panel">
            <h3>Documents</h3>


            {documents.length === 0 ? (
              <p>No documents uploaded yet.</p>
            ) : (
              <ul className="documents-list">
                {documents.map((document) => (
                  <li
                    key={document.id}
                    className="document-list-item"
                  >
                    <span className="document-filename">
                      {document.filename}
                    </span>

                    <button
                      className="document-delete-btn"
                      style={{
                        opacity:
                          deletingDocument &&
                          deleteDocumentId === document.id
                            ? 0.7
                            : 1,
                      }}

                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteDocument(document.id);
                      }}
                      disabled={deletingDocument && deleteDocumentId === document.id}
                      aria-label={`Delete ${document.filename}`}
                      title="Delete document"
                    >
                      🗑️
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {!selectedSession ? (
        <div className="empty-state">
          <div className="empty-content">
            <h1>DocuMind</h1>
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
            <MessageBubble
              key={message.id}
              message={message}
            />
          ))}

          {loading && (
            <div className="message-row assistant-row">
              <div className="message-bubble assistant-bubble">
                <strong>Assistant</strong>
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
