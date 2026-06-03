import "./Sidebar.css";

function Sidebar() {
  return (
    <div className="sidebar">
      <h2 className="logo">🧠 DocuMind</h2>

      <button className="new-chat-btn">
        + New Chat
      </button>

      <div>
        <h4 className="sessions-title">
          Recent Sessions
        </h4>

        <div className="session-item">
          Machine Learning Notes
        </div>

        <div className="session-item">
          DBMS Notes
        </div>

        <div className="session-item">
          Research Paper
        </div>
      </div>

      <div className="profile-section">
        <div className="username">
          Shank
        </div>

        <button className="logout-btn">
          Logout
        </button>
      </div>
    </div>
  );
}

export default Sidebar;