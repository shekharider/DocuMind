import { useEffect, useState } from "react";

import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";

import { getCurrentUser } from "../api/userApi";
import {
  getSessions,
  createSession,
  getMessages,
  askQuestion,
  renameSession,
  deleteSession,
} from "../api/chatApi";
import {
  getSessionDocuments,
  uploadDocument,
  deleteDocument,
} from "../api/documentApi";

function Dashboard() {
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [showDocuments, setShowDocuments] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deleteDocumentId, setDeleteDocumentId] = useState(null);
  const [deletingDocument, setDeletingDocument] = useState(false);


  const loadMessages = async (sessionId) => {
    try {
      const data = await getMessages(sessionId);
      setMessages(data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadDocuments = async (sessionId) => {
    try {
      const data = await getSessionDocuments(sessionId);
      setDocuments(data);
    } catch (error) {
      console.error(error);
      setDocuments([]);
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

  useEffect(() => {
    if (selectedSession) {
      loadDocuments(selectedSession.id);
    } else {
      setDocuments([]);
    }
  }, [selectedSession]);

  const handleSelectSession = async (session) => {
    setSelectedSession(session);
    setShowDocuments(false);
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

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);

      // Refresh sessions and select a valid one
      await loadSessions();

      // loadSessions() updates selectedSession/messages indirectly
      // Ensure UI doesn’t keep a deleted session
      if (selectedSession && selectedSession.id === sessionId) {
        setSelectedSession(null);
        setMessages([]);
      }

      alert("Session deleted successfully");
    } catch (error) {
      console.error(error);
      alert("Failed to delete session");
    }
  };

  const handleRenameSession = async (sessionId, title) => {
    try {
      await renameSession(sessionId, title);
      
      setSessions((currentSessions) =>
        currentSessions.map((session) =>
          session.id === sessionId
            ? {
                ...session,
                title,
              }
            : session
        )
      );

      setSelectedSession((currentSession) =>
        currentSession?.id === sessionId
          ? {
              ...currentSession,
              title,
            }
          : currentSession
      );
    } catch (error) {
      console.error(error);
      alert("Failed to rename session");
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

  const handleDeleteDocument = async (documentId) => {
    if (!documentId) return;
    if (!selectedSession) return;

    try {
      setDeletingDocument(true);
      await deleteDocument(documentId);
      await loadDocuments(selectedSession.id);

      setDeleteDocumentId(null);
      alert("Document deleted successfully");
    } catch (error) {
      console.error(error);
      alert("Failed to delete document");
    } finally {
      setDeletingDocument(false);
    }
  };

  const handleUpload = async (file) => {

    if (!selectedSession || !file) {
      return;
    }

    try {
      setUploading(true);

      await uploadDocument(
        selectedSession.id,
        file
      );

      await loadDocuments(selectedSession.id);
      alert("Document uploaded successfully");
    } catch (error) {
      console.error(error);
      alert("Failed to upload document");
    } finally {
      setUploading(false);
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
        onRenameSession={handleRenameSession}
        onDeleteSession={handleDeleteSession}
      />

      <ChatWindow
        selectedSession={selectedSession}
        messages={messages}
        question={question}
        setQuestion={setQuestion}
        handleSendMessage={handleSendMessage}
        loading={loading}
        documents={documents}
        showDocuments={showDocuments}
        setShowDocuments={setShowDocuments}
        handleUpload={handleUpload}
        uploading={uploading}
        deleteDocumentId={deleteDocumentId}
        deletingDocument={deletingDocument}
        onDeleteDocument={handleDeleteDocument}
      />
    </div>
  );
}

export default Dashboard;
