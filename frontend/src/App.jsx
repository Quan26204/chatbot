import { useEffect, useRef, useState } from "react";
import "./App.css";
import DocumentUpload from "./components/DocumentUpload";

const API_URL = "http://localhost:8000";

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentId, setCurrentId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  async function loadConversations() {
    try {
      const response = await fetch(
        `${API_URL}/conversations`
      );

      if (!response.ok) {
        throw new Error("Failed to load conversations");
      }

      const data = await response.json();

      setConversations(data);
    } catch (error) {
      console.error(error);
    }
  }

  async function createConversation() {
    try {
      const response = await fetch(
        `${API_URL}/conversations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: "New conversation",
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to create conversation");
      }

      const conversation = await response.json();

      setConversations((prev) => [
        conversation,
        ...prev,
      ]);

      setCurrentId(conversation.id);
      setMessages([]);
    } catch (error) {
      console.error(error);
    }
  }

  async function selectConversation(id) {
    try {
      const response = await fetch(
        `${API_URL}/conversations/${id}`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load conversation"
        );
      }

      const data = await response.json();

      setCurrentId(id);
      setMessages(data.messages || []);
    } catch (error) {
      console.error(error);
    }
  }

  async function deleteConversation(id) {
    try {
      const response = await fetch(
        `${API_URL}/conversations/${id}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to delete conversation"
        );
      }

      setConversations((prev) =>
        prev.filter(
          (conversation) =>
            conversation.id !== id
        )
      );

      if (currentId === id) {
        setCurrentId(null);
        setMessages([]);
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function sendMessage() {
    const text = input.trim();

    if (!text || loading) {
      return;
    }

    let conversationId = currentId;

    /*
     * Create conversation automatically
     * if there isn't one yet.
     */
    if (!conversationId) {
      try {
        const response = await fetch(
          `${API_URL}/conversations`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              title:
                text.length > 40
                  ? text.substring(0, 40) + "..."
                  : text,
            }),
          }
        );

        if (!response.ok) {
          throw new Error(
            "Failed to create conversation"
          );
        }

        const conversation =
          await response.json();

        conversationId = conversation.id;

        setCurrentId(conversationId);

        setConversations((prev) => [
          conversation,
          ...prev,
        ]);
      } catch (error) {
        console.error(error);
        return;
      }
    }

    const userMessage = {
      role: "user",
      content: text,
    };

    setMessages((prev) => [
      ...prev,
      userMessage,
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            conversation_id: conversationId,
            message: text,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Chat request failed"
        );
      }

      if (!response.body) {
        throw new Error(
          "No response body"
        );
      }

      const reader =
        response.body.getReader();

      const decoder =
        new TextDecoder();

      let assistantText = "";

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "",
        },
      ]);

      while (true) {
        const { value, done } =
          await reader.read();

        if (done) {
          break;
        }

        const chunk =
          decoder.decode(value, {
            stream: true,
          });

        assistantText += chunk;

        setMessages((prev) => {
          const updated = [...prev];

          updated[
            updated.length - 1
          ] = {
            role: "assistant",
            content: assistantText,
          };

          return updated;
        });
      }
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, something went wrong.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="app">

      {/* =====================================================
          SIDEBAR
          ===================================================== */}

      <aside className="sidebar">

        <div className="sidebar-header">

          <h1>Local AI</h1>

          <button
            className="new-chat"
            onClick={createConversation}
          >
            + New Chat
          </button>

        </div>

        <div className="conversation-list">

          {conversations.length === 0 && (
            <div className="empty-sidebar">
              No conversations yet
            </div>
          )}

          {conversations.map(
            (conversation) => (
              <div
                key={conversation.id}
                className={`conversation ${
                  currentId ===
                  conversation.id
                    ? "active"
                    : ""
                }`}
              >

                <button
                  className="conversation-button"
                  onClick={() =>
                    selectConversation(
                      conversation.id
                    )
                  }
                >
                  {conversation.title ||
                    "New conversation"}
                </button>

                <button
                  className="delete-button"
                  onClick={() =>
                    deleteConversation(
                      conversation.id
                    )
                  }
                >
                  ×
                </button>

              </div>
            )
          )}

        </div>

      </aside>

      {/* =====================================================
          MAIN CHAT
          ===================================================== */}

      <main className="chat">

        <header className="chat-header">

          <div>

            <h2>AI Assistant</h2>

            <span>
              Qwen3:8B · RAG
            </span>

          </div>

        </header>

        {/* ===================================================
            MESSAGES
            =================================================== */}

        <div className="messages">

          {messages.length === 0 && (
            <div className="welcome">

              <h1>
                How can I help you?
              </h1>

              <p>
                Ask questions about your
                documents or start a
                conversation.
              </p>

            </div>
          )}

          {messages.map(
            (message, index) => (
              <div
                key={index}
                className={`message-row ${
                  message.role
                }`}
              >

                <div className="message">

                  <div className="message-role">

                    {message.role ===
                    "user"
                      ? "You"
                      : "AI"}

                  </div>

                  <div className="message-content">
                    {message.content}
                  </div>

                </div>

              </div>
            )
          )}

          {loading && (
            <div className="typing">
              AI is thinking...
            </div>
          )}

          <div
            ref={messagesEndRef}
          />

        </div>

        {/* ===================================================
            INPUT
            =================================================== */}

        <div className="input-area">

          <div className="input-box">

            {/* PDF UPLOAD */}

            <DocumentUpload />

            {/* MESSAGE INPUT */}

            <textarea
              value={input}
              onChange={(event) =>
                setInput(
                  event.target.value
                )
              }
              onKeyDown={handleKeyDown}
              placeholder="Ask something..."
              rows={1}
              disabled={loading}
            />

            {/* SEND */}

            <button
              onClick={sendMessage}
              disabled={
                loading ||
                !input.trim()
              }
            >
              ↑
            </button>

          </div>

          <div className="input-hint">
            Enter to send · Shift + Enter
            for new line
          </div>

        </div>

      </main>

    </div>
  );
}

export default App;