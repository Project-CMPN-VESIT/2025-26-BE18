import React, { useState, useRef, useEffect } from "react";
import DataVisualization from "./DataVisualization";

const NormalPage = () => {
  const [sessions, setSessions] = useState([
    { id: 1, name: "New Chat", messages: [], createdAt: new Date() },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState(1);
  const [showVisualization, setShowVisualization] = useState(false);
  const [visualizationData, setVisualizationData] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mode, setMode] = useState("normal"); // 'normal', 'pdf', 'borewell'
  const [file, setFile] = useState(null);
  const [coordinates, setCoordinates] = useState({ lat: "", long: "" });
  const messagesEndRef = useRef(null);

  const PREDEFINED_RESPONSES = {
    "Is borewell drilling feasible in my location?": {
      text: `### Borewell Drilling Feasibility in Shirol Taluka
      **Recommendation: YES – Drilling is feasible and recommended**
      **Key Findings:**
      - **Current Groundwater Level**: 18–25 meters (Post-monsoon: ~16–22m)
      - **Geology**: Deccan Basalt with good fracture zones up to 200m depth
      - **Success Rate**: 92% of borewells drilled in the last 5 years yielded water
      - **Recommended Depth**: 180–250 feet (55–75 meters)
      - **Yield Expectation**: 1.5–4 inches (average 2.8 inches)
      - **Water Quality**: Generally potable with TDS < 800 mg/L
      **Best Time for Drilling**: February – May (pre-monsoon)
      **Note**: Hydrogeological survey using scientific methods is advised before final site selection.
      **Status**: SAFE Category | Extraction: 38.57% | Recharge > Draft`,
      parsedData: {
        title: "Borewell Feasibility Report - Shirol",
        metadata: {
          timestamp: new Date().toLocaleString(),
          location: "Shirol, Maharashtra",
          depth: "180–250 ft",
          quality: "Potable (TDS < 800 mg/L)",
          status: "Recommended",
        },
        sections: [
          {
            title: "Summary",
            content: ["Borewell drilling is highly feasible", "High success rate in the region"],
            type: "info",
          },
          {
            title: "Geological Conditions",
            content: ["Deccan Trap Basalt", "Good secondary porosity", "Fractured aquifers present"],
            type: "info",
          },
          {
            title: "Expected Yield",
            content: ["Average: 2.8 inches", "Range: 1.5–4.0 inches", "Sustainable pumping: 8–10 hours/day"],
            type: "general",
          },
        ],
      },
    },
    "Show me rainfall and recharge trends for my region": {
      text: `### Rainfall & Recharge Trends - Shirol Taluka (2018–2024)
      **Annual Average Rainfall**: 785 mm
      **Monsoon Contribution**: 92% (June–September)
      **Peak Rainfall Month**: July (avg. 320 mm)
      **Groundwater Recharge Trend**:
      - 2018 → 2024: +18.4% increase in recharge
      - Monsoon recharge efficiency: 24–32%
      - Total annual recharge: ~11,476 MCM
      **Seasonal Water Level Fluctuation**:
      - Pre-monsoon: 18.2m → Post-monsoon: 16.8m (rise of ~1.4m avg.)
      - Recovery rate: Full recovery observed in 94% of wells
      **Trend**: Positive – Groundwater levels are stable and improving due to good rainfall and conservation efforts.
      **Visualization Available Below**`,
      parsedData: {
        title: "Rainfall & Recharge Trends - Shirol",
        metadata: {
          timestamp: new Date().toLocaleString(),
          location: "Shirol Taluka",
          depth: "Improving",
          quality: "Stable",
          status: "Positive Trend",
        },
        sections: [
          {
            title: "Rainfall Summary",
            content: ["Average: 785 mm/year", "92% from Monsoon", "July highest (320 mm)"],
            type: "info",
          },
          {
            title: "Recharge Performance",
            content: ["+18.4% increase since 2018", "Monsoon efficiency: 24–32%", "Full recovery in 94% wells"],
            type: "info",
          },
          {
            title: "Water Level Trend",
            content: ["Pre-monsoon: ~18.2m", "Post-monsoon: ~16.8m", "Annual rise: ~1.4m"],
            type: "general",
          },
        ],
      },
    },
  };

  const currentSession = sessions.find((s) => s.id === currentSessionId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages]);

  const createNewSession = () => {
    const newSession = {
      id: Date.now(),
      name: "New Chat",
      messages: [],
      createdAt: new Date(),
    };
    setSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  const updateSessionName = (sessionId, firstMessage) => {
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              name:
                firstMessage.slice(0, 30) +
                (firstMessage.length > 30 ? "..." : ""),
            }
          : session
      )
    );
  };

  const handleFileUpload = (e) => {
    setFile(e.target.files[0]);
  };

  const handleCoordinatesChange = (e) => {
    const { name, value } = e.target;
    setCoordinates((prev) => ({ ...prev, [name]: value }));
  };

  const sendQueryToAPI = async (query, mode) => {
    try {
      let endpoint = "";
      let body = {};
      let response;

      if (mode === "normal") {
        endpoint = "http://127.0.0.1:5000/process_groundwater_query";
        body = { query };
      } else if (mode === "pdf") {
        if (!file) {
          return { error: "Please upload a PDF file." };
        }
        endpoint = "http://127.0.0.1:5000/get_summary";
        body = { file_url: URL.createObjectURL(file) };
      } else if (mode === "borewell") {
        if (!coordinates.lat || !coordinates.long) {
          return { error: "Please enter latitude and longitude." };
        }
        endpoint = "http://127.0.0.1:5000/borewell_analysis";
        body = { latitude: coordinates.lat, longitude: coordinates.long };
      }

      response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      return await response.json();
    } catch (error) {
      console.error("Error calling API:", error);
      return { error: "Sorry, I encountered an error processing your request." };
    }
  };

  const handleSendMessage = async () => {
    if (isLoading) return;

    let userMessageText = "";
    if (mode === "normal") {
      if (inputValue.trim() === "") return;
      userMessageText = inputValue;
    } else if (mode === "pdf") {
      if (!file) return;
      userMessageText = "PDF uploaded";
    } else if (mode === "borewell") {
      if (!coordinates.lat || !coordinates.long) return;
      userMessageText = `Borewell analysis for ${coordinates.lat}, ${coordinates.long}`;
    }

    const userMessage = {
      id: Date.now(),
      text: userMessageText,
      sender: "user",
      timestamp: new Date(),
    };

    setSessions((prev) =>
      prev.map((session) =>
        session.id === currentSessionId
          ? { ...session, messages: [...session.messages, userMessage] }
          : session
      )
    );

    if (currentSession.messages.length === 0) {
      updateSessionName(currentSessionId, userMessageText);
    }

    setInputValue("");
    setIsLoading(true);

    const apiResponse = await sendQueryToAPI(inputValue, mode);
    const responseText = apiResponse.error || JSON.stringify(apiResponse, null, 2);

    const botMessage = {
      id: Date.now() + 1,
      text: responseText,
      sender: "bot",
      timestamp: new Date(),
      reportUrl: apiResponse.report_url,
    };

    setSessions((prev) =>
      prev.map((session) =>
        session.id === currentSessionId
          ? { ...session, messages: [...session.messages, botMessage] }
          : session
      )
    );

    setIsLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const formatDate = (date) => {
    const today = new Date();
    const messageDate = new Date(date);
    if (messageDate.toDateString() === today.toDateString()) return "Today";
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (messageDate.toDateString() === yesterday.toDateString()) return "Yesterday";
    return messageDate.toLocaleDateString();
  };

  const FormattedResponse = ({ message }) => {
    const { parsedData } = message;

    if (!parsedData || !parsedData.sections.length) {
      return <div>{message.text}</div>;
    }

    return (
      <div style={{ width: "100%" }}>
        {/* Visualization Toggle Button */}
        <div style={{ marginBottom: "12px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <button
            onClick={() => {
              setShowVisualization(!showVisualization);
              setVisualizationData({
                query: message.userQuery,
                response: message.text,
                parsedData: parsedData,
              });
            }}
            style={{
              background: showVisualization && visualizationData?.query === message.userQuery
                ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
                : "linear-gradient(135deg, #8b5cf6, #6366f1)",
              color: "white",
              border: "none",
              padding: "10px 16px",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: "600",
              cursor: "pointer",
              transition: "all 0.2s ease",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: "0 2px 4px rgba(139, 92, 246, 0.3)",
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = "translateY(-1px)";
              e.target.style.boxShadow = "0 4px 12px rgba(139, 92, 246, 0.4)";
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = "translateY(0)";
              e.target.style.boxShadow = "0 2px 4px rgba(139, 92, 246, 0.3)";
            }}
          >
            📊 {showVisualization && visualizationData?.query === message.userQuery ? "Hide" : "Show"} Visualization
          </button>
        </div>

        {/* Visualization Component */}
        {showVisualization && visualizationData?.query === message.userQuery && (
          <div
            style={{
              marginBottom: "16px",
              backgroundColor: "#f9fafb",
              borderRadius: "12px",
              padding: "16px",
              border: "2px solid #e5e7eb",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
            }}
          >
            <DataVisualization
              query={message.userQuery}
              apiResponse={message.text}
            />
          </div>
        )}

        {/* Header Card */}
        <div
          style={{
            background: "linear-gradient(135deg, #3b82f6, #1d4ed8)",
            color: "white",
            padding: "16px",
            borderRadius: "12px",
            marginBottom: "16px",
            textAlign: "center",
          }}
        >
          <h3
            style={{ margin: "0 0 8px 0", fontSize: "16px", fontWeight: "600" }}
          >
            {parsedData.title}
          </h3>
          <p style={{ margin: 0, fontSize: "12px", opacity: 0.9 }}>
            Generated on {parsedData.metadata.timestamp}
          </p>
        </div>

        {/* Metadata Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
            gap: "8px",
            marginBottom: "16px",
          }}
        >
          {Object.entries(parsedData.metadata)
            .filter(
              ([key, value]) =>
                key !== "timestamp" &&
                value !== "N/A" &&
                value !== "Not specified"
            )
            .map(([key, value]) => (
              <div
                key={key}
                style={{
                  background: "#f0f9ff",
                  border: "1px solid #e0f2fe",
                  borderRadius: "8px",
                  padding: "8px",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontSize: "10px",
                    color: "#0369a1",
                    fontWeight: "600",
                    textTransform: "uppercase",
                  }}
                >
                  {key}
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    color: "#1e40af",
                    fontWeight: "500",
                    marginTop: "2px",
                  }}
                >
                  {value}
                </div>
              </div>
            ))}
        </div>

        {/* Content Sections */}
        {parsedData.sections.map((section, index) => (
          <div
            key={index}
            style={{
              background: section.type === "info" ? "#fef3c7" : "#f3f4f6",
              border: `1px solid ${
                section.type === "info" ? "#fbbf24" : "#d1d5db"
              }`,
              borderRadius: "8px",
              padding: "12px",
              marginBottom: "12px",
              borderLeft: `4px solid ${
                section.type === "info" ? "#f59e0b" : "#6b7280"
              }`,
            }}
          >
            <h4
              style={{
                margin: "0 0 8px 0",
                fontSize: "14px",
                fontWeight: "600",
                color: section.type === "info" ? "#92400e" : "#374151",
              }}
            >
              {section.title}
            </h4>
            {section.content.map((item, itemIndex) => (
              <div
                key={itemIndex}
                style={{
                  fontSize: "13px",
                  lineHeight: "1.5",
                  color: section.type === "info" ? "#92400e" : "#4b5563",
                  marginBottom:
                    itemIndex < section.content.length - 1 ? "4px" : 0,
                }}
              >
                {item}
              </div>
            ))}
          </div>
        ))}

        {/* Simple Visualization */}
        {parsedData.metadata.status !== "N/A" && (
          <div
            style={{
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "12px",
              marginTop: "12px",
            }}
          >
            <h4
              style={{
                margin: "0 0 8px 0",
                fontSize: "14px",
                fontWeight: "600",
                color: "#374151",
              }}
            >
              Status Overview
            </h4>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div
                style={{
                  width: "12px",
                  height: "12px",
                  borderRadius: "50%",
                  background:
                    parsedData.metadata.status.toLowerCase().includes("good") ||
                    parsedData.metadata.status
                      .toLowerCase()
                      .includes("available")
                      ? "#10b981"
                      : "#ef4444",
                }}
              />
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: "500",
                  color: "#374151",
                }}
              >
                {parsedData.metadata.status}
              </span>
            </div>
          </div>
        )}
      </div>
    );
  };

  const downloadPDF = async (message) => {
    // Your existing downloadPDF function
  };

  return (
    <>
      <style jsx>{`
        .chatbot-container {
          position: relative;
          height: 100vh;
          width: 100vw;
          overflow: hidden;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto",
            "Oxygen", "Ubuntu", "Cantarell", sans-serif;
          margin: 0;
          padding: 0;
        }
        /* ... (rest of your existing styles) ... */
        .mode-switcher {
          display: flex;
          background-color: #e5e7eb;
          padding: 8px;
          border-radius: 8px;
          margin: 12px;
          gap: 8px;
        }
        .mode-switcher button {
          flex: 1;
          padding: 8px 12px;
          border: none;
          background: none;
          cursor: pointer;
          border-radius: 6px;
          font-weight: 500;
          transition: all 0.2s;
        }
        .mode-switcher button.active {
          background-color: #2563eb;
          color: white;
        }
        .coordinates-input {
          display: flex;
          gap: 8px;
        }
        .coordinates-input input {
          flex: 1;
          padding: 12px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
        }
      `}</style>

      <div className="chatbot-container">
        {/* Background */}
        <iframe
          src="https://ingres.iith.ac.in/home"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            width: "100vw",
            height: "100vh",
            border: "none",
            zIndex: -2,
          }}
          title="INGRO Background"
        />
        <div className="background-overlay" />

        {/* Chat Toggle Button */}
        <button
          onClick={() => setChatOpen(!chatOpen)}
          className="chat-toggle-btn"
        >
          {chatOpen ? "✕" : "💬"}
        </button>

        {/* Chat Interface */}
        <div
          className={`chat-interface ${chatOpen ? "chat-open" : "chat-closed"}`}
        >
          {/* Sidebar */}
          <div
            className={`sidebar ${
              sidebarOpen ? "sidebar-open" : "sidebar-closed"
            }`}
          >
            {/* ... (rest of your sidebar code) ... */}
          </div>

          {/* Main Chat Panel */}
          <div
            style={{
              flex: 1,
              backgroundColor: "white",
              display: "flex",
              flexDirection: "column",
              height: "100vh",
              minWidth: 0,
            }}
          >
            {/* Header */}
            {/* ... (rest of your header code) ... */}

            {/* Welcome Banner */}
            {/* ... (rest of your welcome banner code) ... */}

            {/* Messages Container */}
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "16px",
                backgroundColor: "#f9fafb",
              }}
            >
              {/* ... (rest of your messages container code) ... */}
            </div>

            {/* Input Area */}
            <div
              style={{
                padding: "16px",
                backgroundColor: "white",
                borderTop: "1px solid #e5e7eb",
              }}
            >
              <div className="mode-switcher">
                <button
                  className={mode === "normal" ? "active" : ""}
                  onClick={() => setMode("normal")}
                >
                  Normal Query
                </button>
                <button
                  className={mode === "pdf" ? "active" : ""}
                  onClick={() => setMode("pdf")}
                >
                  PDF Visualization
                </button>
                <button
                  className={mode === "borewell" ? "active" : ""}
                  onClick={() => setMode("borewell")}
                >
                  Borewell Report
                </button>
              </div>

              <div
                style={{ display: "flex", alignItems: "flex-end", gap: "12px", marginTop: "12px" }}
              >
                {mode === "normal" && (
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about groundwater resources..."
                    disabled={isLoading}
                    style={{
                      flex: 1,
                      padding: "12px 16px",
                      border: "2px solid #d1d5db",
                      borderRadius: "16px",
                      resize: "none",
                      outline: "none",
                      fontSize: "14px",
                      minHeight: "48px",
                      maxHeight: "120px",
                      fontFamily: "inherit",
                      transition: "border-color 0.2s",
                      opacity: isLoading ? 0.5 : 1,
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = "#2563eb";
                      e.target.style.boxShadow = "0 0 0 3px rgba(37, 99, 235, 0.1)";
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = "#d1d5db";
                      e.target.style.boxShadow = "none";
                    }}
                    rows={1}
                  />
                )}
                {mode === "pdf" && (
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileUpload}
                    style={{
                      flex: 1,
                      padding: "12px 16px",
                      border: "2px solid #d1d5db",
                      borderRadius: "16px",
                      outline: "none",
                      fontSize: "14px",
                      minHeight: "48px",
                    }}
                  />
                )}
                {mode === "borewell" && (
                  <div className="coordinates-input" style={{ flex: 1, display: "flex", gap: "8px" }}>
                    <input
                      type="text"
                      name="lat"
                      placeholder="Latitude"
                      value={coordinates.lat}
                      onChange={handleCoordinatesChange}
                      style={{
                        flex: 1,
                        padding: "12px 16px",
                        border: "2px solid #d1d5db",
                        borderRadius: "16px",
                        outline: "none",
                        fontSize: "14px",
                        minHeight: "48px",
                      }}
                    />
                    <input
                      type="text"
                      name="long"
                      placeholder="Longitude"
                      value={coordinates.long}
                      onChange={handleCoordinatesChange}
                      style={{
                        flex: 1,
                        padding: "12px 16px",
                        border: "2px solid #d1d5db",
                        borderRadius: "16px",
                        outline: "none",
                        fontSize: "14px",
                        minHeight: "48px",
                      }}
                    />
                  </div>
                )}
                <button
                  onClick={handleSendMessage}
                  disabled={isLoading}
                  style={{
                    padding: "12px 16px",
                    borderRadius: "16px",
                    border: "none",
                    cursor: isLoading ? "not-allowed" : "pointer",
                    transition: "all 0.2s",
                    backgroundColor: isLoading ? "#d1d5db" : "#2563eb",
                    color: isLoading ? "#6b7280" : "white",
                    fontWeight: "600",
                    fontSize: "14px",
                    boxShadow: isLoading ? "none" : "0 4px 12px rgba(37, 99, 235, 0.3)",
                  }}
                >
                  {isLoading ? "..." : "Send ➤"}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Overlay */}
        {chatOpen && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              backgroundColor: "rgba(0,0,0,0.5)",
              zIndex: 30,
            }}
            onClick={() => setChatOpen(false)}
          />
        )}
      </div>
    </>
  );
};

export default NormalPage;
