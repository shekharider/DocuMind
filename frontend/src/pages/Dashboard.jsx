import { useEffect, useState } from "react";

import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";

import { getCurrentUser } from "../api/userApi";
import { getSessions, createSession } from "../api/chatApi";

function Dashboard() {
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);

  const loadSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    const loadUser = async () => {
      try {
        const data = await getCurrentUser();
        setUser(data);
      } catch (error) {
        console.error(error);
      }
    };

    loadUser();
    loadSessions();
  }, []);

  const handleCreateSession = async () => {
    try {
      await createSession("New Chat");
      await loadSessions();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
      }}
    >
      <Sidebar
        user={user}
        sessions={sessions}
        onCreateSession={handleCreateSession}
      />

      <ChatWindow />
    </div>
  );
}

export default Dashboard;