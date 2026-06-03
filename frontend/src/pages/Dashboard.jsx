import { useEffect, useState } from "react";

import Sidebar from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";

import { getCurrentUser }
from "../api/userApi";

function Dashboard() {

  const [user, setUser] =
    useState(null);

  useEffect(() => {

    const loadUser = async () => {

      try {

        const data =
          await getCurrentUser();

        setUser(data);

      } catch (error) {

        console.log(error);

      }
    };

    loadUser();

  }, []);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
      }}
    >
      <Sidebar user={user} />

      <ChatWindow />
    </div>
  );
}

export default Dashboard;