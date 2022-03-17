import { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [userMessage, setUserMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      text: "Hi there! I am DeBot, how can I help you today?",
      sender: "bot",
    },
  ]);

  const messagesEndRef = useRef(null);

  const updateUserMessage = (event) => {
    setUserMessage(event.target.value);
  };

  const sendMessage = (e) => {
    if (e.type !== "keydown" || e.key === "Enter") {
      const allMessages = [...messages, { text: userMessage, sender: "user" }];
      setMessages(allMessages);
      setUserMessage("");

      fetch(`/send-message/${userMessage}`, {
        method: "POST",
      })
        .then((res) => res.json())
        .then((response) => {
          response.messages.forEach((message) => {
            setMessages([...allMessages, { text: message, sender: "bot" }]);
          });
        });
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="app">
      <div className="chatArea">
        <div className="messagesArea">
          {messages.map((message, index) => (
            <div
              className={
                "message " +
                (message.sender === "bot" ? "botMessage" : "userMessage")
              }
              key={index}
            >
              <span>{message.text}</span>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <textarea
          className="textArea"
          placeholder="Write a message..."
          onChange={updateUserMessage}
          onKeyDown={sendMessage}
          value={userMessage}
        />

        <button
          className="sendButton"
          onClick={sendMessage}
          disabled={!userMessage}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
