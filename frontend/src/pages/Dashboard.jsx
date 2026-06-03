import { useEffect, useState } from "react";

import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";

import { getCurrentUser } from "../api/userApi";
import {
  getSessions,
  createSession,
  getMessages,
  askQuestion,
} from "../api/chatApi";

function Dashboard() {
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  const loadMessages = async (sessionId) => {
    try {
      const data = await getMessages(sessionId);
      setMessages(data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data);

      if (data.length > 0 && !selectedSession) {
        setSelectedSession(data[0]);
        await loadMessages(data[0].id);
      }
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

  const handleSelectSession = async (session) => {
    setSelectedSession(session);
    await loadMessages(session.id);
  };

  const handleCreateSession = async () => {
    try {
      await createSession("New Chat");
      await loadSessions();
    } catch (error) {
      console.error(error);
    }
  };

  const handleSendMessage = async () => {
    if (!selectedSession || !question.trim()) {
      return;
    }

    try {
      setLoading(true);

      await askQuestion(
        selectedSession.id,
        question
      );

      await loadMessages(selectedSession.id);
      setQuestion("");
    } catch (error) {
      console.error(error);
      alert("Failed to get answer");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
      }}
    >
      <Sidebar
        user={user}
        sessions={sessions}
        onCreateSession={handleCreateSession}
        selectedSession={selectedSession}
        onSelectSession={handleSelectSession}
      />

      <ChatWindow
        selectedSession={selectedSession}
        messages={messages}
        question={question}
        setQuestion={setQuestion}
        handleSendMessage={handleSendMessage}
        loading={loading}
      />
    </div>
  );
}

export default Dashboard;
