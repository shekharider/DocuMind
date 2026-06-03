import "./Sidebar.css";

function Sidebar({ user, sessions, onCreateSession }) {
  return (
    <div className="sidebar">
      <h2 className="logo">🧠 DocuMind</h2>

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
            className="session-item"
          >
            {session.title}
          </div>
        ))}
      </div>

      <div className="profile-section">
        <div className="username">
          {user?.username}
        </div>

        <button className="logout-btn"
        onClick={handleLogout}
        >
          Logout
        </button>
      </div>
    </div>
  );
}

const handleLogout = () => {

  localStorage.removeItem(
    "token"
  );

  window.location.href =
    "/login";
};

export default Sidebar;