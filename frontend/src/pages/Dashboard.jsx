import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";

function Dashboard() {
  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
      }}
    >
      <Sidebar />
      <ChatWindow />
    </div>
  );
}

export default Dashboard;