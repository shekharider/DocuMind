import { useState } from "react";

import "./Sidebar.css";
import ConfirmModal from "./ConfirmModal";
import SessionMenu from "./SessionMenu";


function Sidebar({
  user,
  sessions,
  onCreateSession,
  selectedSession,
  onSelectSession,
  onRenameSession,
  onDeleteSession,
}) {
  const [openMenuId, setOpenMenuId] = useState(null);
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [deleteSession, setDeleteSession] = useState(null);

  const startRename = (session) => {
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const saveRename = () => {
    const title = editingTitle.trim();

    if (editingSessionId && title) {
      onRenameSession(editingSessionId, title);
    }

    setEditingSessionId(null);
    setEditingTitle("");
  };

  const cancelRename = () => {
    setEditingSessionId(null);
    setEditingTitle("");
  };

  const handleDeleteSession = async (session) => {
    // UI confirmation handled by ConfirmModal (already present); here we just call API if available.
    // Since current app didn't previously implement delete, keep it minimal.
    try {
      // lazy import to avoid circular deps
      const { deleteSession } = await import("../api/chatApi");
      await deleteSession(session.id);
      window.location.reload();
    } catch (e) {
      console.error(e);
      alert("Failed to delete session");
    }
  };

  return (
    <div className="sidebar">
      <h2 className="logo">DocuMind</h2>

      <button
        className="new-chat-btn"
        onClick={onCreateSession}
      >
        + New Chat
      </button>

      <div>
        <h4 className="sessions-title">
          Recent Sessions
        </h4>

        {sessions?.map((session) => (
          <div
            key={session.id}
            className={`session-item ${
              selectedSession?.id === session.id
                ? "active"
                : ""
            }`}
            onClick={() => onSelectSession(session)}
          >
            {editingSessionId === session.id ? (
              <input
                className="session-rename-input"
                value={editingTitle}
                autoFocus
                onClick={(e) => e.stopPropagation()}
                onChange={(e) =>
                  setEditingTitle(e.target.value)
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    saveRename();
                  }

                  if (e.key === "Escape") {
                    cancelRename();
                  }
                }}
                onBlur={saveRename}
              />
            ) : (
              <>
                <span className="session-title">
                  {session.title}
                </span>

                <SessionMenu
                  session={session}
                  isOpen={openMenuId === session.id}
                  onOpen={setOpenMenuId}
                  onClose={() => setOpenMenuId(null)}
                  onRename={startRename}
                  onDelete={(session) => {
                    setDeleteSession(session);
                  }}

                />
              </>
            )}
          </div>
        ))}
      </div>

      <div className="profile-section">
        <div className="username">
          {user?.username}
        </div>

        <button
          className="logout-btn"
          onClick={handleLogout}
        >
          Logout
        </button>
      </div>

      <ConfirmModal
        open={Boolean(deleteSession)}
        title="Delete Session?"
        body="This action will permanently remove the session and all associated data."
        onCancel={() => setDeleteSession(null)}
        onConfirm={() => {
          if (deleteSession) {
            onDeleteSession(deleteSession.id);
          }
          setDeleteSession(null);
        }}
      />
    </div>
  );
}

const handleLogout = () => {
  localStorage.removeItem("token");
  window.location.href = "/login";
};

export default Sidebar;
