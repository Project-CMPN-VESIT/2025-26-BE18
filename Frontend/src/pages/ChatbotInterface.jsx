import React, { useState, useRef, useEffect } from "react";

const ChatbotInterface = () => {
  const [sessions, setSessions] = useState([
    { id: 1, name: "New Chat", messages: [], createdAt: new Date() },
  ]);
  const [currentSessionId, setCurrentSessionId] = useState(1);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentMode, setCurrentMode] = useState("normal");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

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
    setCurrentMode("normal");
    setSelectedFile(null);
    setLatitude("");
    setLongitude("");
  };

  const updateSessionName = (sessionId, firstMessage) => {
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId
          ? { ...session, name: firstMessage.slice(0, 30) + (firstMessage.length > 30 ? "..." : "") }
          : session
      )
    );
  };

  const uploadToCloudinary = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("upload_preset", "ml_default"); // Make sure this preset exists in your Cloudinary settings
    
    try {
      const response = await fetch("https://api.cloudinary.com/v1_1/dyl2ptmmp/image/upload", {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error("Upload failed");
      }
      
      const data = await response.json();
      console.log("Cloudinary upload response:", data);
      return data.secure_url;
    } catch (error) {
      console.error("Cloudinary upload error:", error);
      throw error;
    }
  };

  const sendNormalQuery = async (query) => {
    try {
      const response = await fetch("http://127.0.0.1:5000/process_groundwater_query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      return await response.json();
    } catch (error) {
      return { error: "Sorry, I encountered an error processing your request." };
    }
  };

  const sendPDFAnalysis = async (fileUrl) => {
    try {
      const response = await fetch("http://127.0.0.1:5000/get_summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_url: fileUrl }),
      });
      return await response.json();
    } catch (error) {
      return { error: "Sorry, I encountered an error analyzing the PDF." };
    }
  };

  const sendBorewellAnalysis = async (lat, lon) => {
    try {
      const response = await fetch("http://127.0.0.1:5000/borewell_analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude: lat, longitude: lon }),
      });
      return await response.json();
    } catch (error) {
      return { error: "Sorry, I encountered an error analyzing the borewell data." };
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type === "application/pdf") {
      setSelectedFile(file);
    } else {
      alert("Please select a valid PDF file");
    }
  };

  const handleSendMessage = async () => {
    if (currentMode === "normal") {
      if (inputValue.trim() === "" || isLoading) return;

      const userMessage = { id: Date.now(), text: inputValue, sender: "user", timestamp: new Date() };
      setSessions((prev) =>
        prev.map((s) => (s.id === currentSessionId ? { ...s, messages: [...s.messages, userMessage] } : s))
      );

      if (currentSession.messages.length === 0) updateSessionName(currentSessionId, inputValue);

      const query = inputValue;
      setInputValue("");
      setIsLoading(true);

      const apiResponse = await sendNormalQuery(query);
      const responseText = apiResponse.error || `### Groundwater Analysis Report\n\n**Status**: ${apiResponse.status}\n**Location**: ${apiResponse.location || "N/A"}\n**Data Scope**: ${apiResponse.data_scope || "N/A"}\n\nYour detailed report has been generated successfully.`;

      const botMessage = {
        id: Date.now() + 1,
        text: responseText,
        sender: "bot",
        timestamp: new Date(),
        reportUrl: apiResponse.report_url,
        userQuery: query,
        mode: "normal",
      };

      setSessions((prev) =>
        prev.map((s) => (s.id === currentSessionId ? { ...s, messages: [...s.messages, botMessage] } : s))
      );
      setIsLoading(false);
    } else if (currentMode === "pdf") {
      if (!selectedFile || isLoading) return;

      const userMessage = { id: Date.now(), text: `📄 Analyzing PDF: ${selectedFile.name}`, sender: "user", timestamp: new Date() };
      setSessions((prev) =>
        prev.map((s) => (s.id === currentSessionId ? { ...s, messages: [...s.messages, userMessage] } : s))
      );

      if (currentSession.messages.length === 0) updateSessionName(currentSessionId, `PDF: ${selectedFile.name}`);

      setIsLoading(true);
      setUploadProgress(20);

      try {
        // Step 1: Upload to Cloudinary
        console.log("Uploading PDF to Cloudinary...");
        const fileUrl = await uploadToCloudinary(selectedFile);
        console.log("Cloudinary URL:", fileUrl);
        setUploadProgress(50);

        // Step 2: Send to analysis API
        console.log("Sending to analysis API...");
        const apiResponse = await sendPDFAnalysis(fileUrl);
        console.log("API Response:", apiResponse);
        setUploadProgress(100);

        // Step 3: Display results
        let responseText = "";
        if (apiResponse.error) {
          responseText = apiResponse.error;
        } else {
          responseText = `### PDF Analysis Complete\n\n**File**: ${selectedFile.name}\n**Status**: ${apiResponse.message || "Success"}\n**File URL**: ${fileUrl}\n\nYour PDF has been analyzed successfully. Click the button below to view the detailed report.`;
        }

        const botMessage = {
          id: Date.now() + 1,
          text: responseText,
          sender: "bot",
          timestamp: new Date(),
          reportUrl: apiResponse.report_url,
          fileUrl: fileUrl,
          mode: "pdf",
        };

        setSessions((prev) =>
          prev.map((s) => (s.id === currentSessionId ? { ...s, messages: [...s.messages, botMessage] } : s))
        );
      } catch (error) {
        console.error("PDF processing error:", error);
        const errorMessage = { 
          id: Date.now() + 1, 
          text: `❌ Error processing PDF: ${error.message || "Unknown error occurred"}\n\nPlease check:\n- Your Cloudinary upload preset is configured correctly\n- The API endpoint is accessible\n- Your file is a valid PDF`, 
          sender: "bot", 
          timestamp: new Date() 
        };
        setSessions((prev) =>
          prev.map((s) => (s.id === currentSessionId ? { ...s, messages: [...s.messages, errorMessage] } : s))
        );
      }

      setIsLoading(false);
      setUploadProgress(0);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } else if (currentMode === "borewell") {
      if (!latitude || !longitude || isLoading) return;

      const userMessage = { id: Date.now(), text: `🗺️ Analyzing Borewell: ${latitude}, ${longitude}`, sender: "user", timestamp: new Date() };
      setSessions((prev) =>
        prev.map((s) => (s.id === currentSessionId ? { ...s, messages: [...s.messages, userMessage] } : s))
      );

      if (currentSession.messages.length === 0) updateSessionName(currentSessionId, `Borewell: ${latitude}, ${longitude}`);

      setIsLoading(true);
      const apiResponse = await sendBorewellAnalysis(latitude, longitude);

      const responseText = apiResponse.error || `### Borewell Analysis Report\n\n**Status**: ${apiResponse.status}\n**District**: ${apiResponse.district || "N/A"}\n**Taluka**: ${apiResponse.taluka || "N/A"}\n**Data Level**: ${apiResponse.data_level_used || "N/A"}\n\nYour borewell analysis has been completed.`;

      const botMessage = {
        id: Date.now() + 1,
        text: responseText,
        sender: "bot",
        timestamp: new Date(),
        reportUrl: apiResponse.report_url,
        mode: "borewell",
      };

      setSessions((prev) =>
        prev.map((s) => (s.id === currentSessionId ? { ...s, messages: [...s.messages, botMessage] } : s))
      );
      setIsLoading(false);
      setLatitude("");
      setLongitude("");
    }
  };

  const formatTime = (ts) => ts.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const formatDate = (date) => {
    const today = new Date();
    const msgDate = new Date(date);
    if (msgDate.toDateString() === today.toDateString()) return "Today";
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (msgDate.toDateString() === yesterday.toDateString()) return "Yesterday";
    return msgDate.toLocaleDateString();
  };

  return (
    <>
      <style>{`
        * { box-sizing: border-box; }
        .chatbot-container { position: relative; height: 100vh; width: 100vw; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; }
        .bg-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: -1; }
        .chat-toggle { position: fixed; bottom: 24px; right: 24px; z-index: 50; background: #2563eb; color: white; padding: 16px; border-radius: 50%; border: none; box-shadow: 0 10px 25px rgba(0,0,0,0.3); cursor: pointer; transition: all 0.3s; font-size: 20px; }
        .chat-toggle:hover { background: #1d4ed8; transform: scale(1.05); }
        .chat-interface { position: fixed; top: 0; right: 0; height: 100vh; z-index: 40; display: flex; transition: transform 0.3s; box-shadow: -10px 0 20px rgba(0,0,0,0.2); }
        .chat-closed { transform: translateX(100%); }
        .chat-open { transform: translateX(0); }
        .sidebar { background: white; border-right: 1px solid #e5e7eb; transition: width 0.3s; overflow: hidden; display: flex; flex-direction: column; }
        .sidebar-closed { width: 0; }
        .sidebar-open { width: 280px; }
        .loading-dots { display: flex; gap: 4px; }
        .loading-dot { width: 8px; height: 8px; border-radius: 50%; background: #2563eb; animation: pulse 1.5s ease-in-out infinite; }
        .loading-dot:nth-child(2) { animation-delay: 0.2s; }
        .loading-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulse { 0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); } 30% { opacity: 1; transform: scale(1); } }
        .msg-anim { animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @media (min-width: 1024px) { .chat-toggle { display: none; } .chat-interface { transform: translateX(0); width: 480px; } }
        @media (max-width: 1023px) { .chat-interface { width: 100vw; max-width: 480px; } }
        @media (max-width: 640px) { .chat-interface { max-width: 100vw; } .sidebar-open { width: 260px; } }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
      `}</style>

      <div className="chatbot-container">
        <iframe src="https://ingres.iith.ac.in/home" style={{ position: "fixed", inset: 0, width: "100vw", height: "100vh", border: "none", zIndex: -2 }} title="BG" />
        <div className="bg-overlay" />
        <button onClick={() => setChatOpen(!chatOpen)} className="chat-toggle">{chatOpen ? "✕" : "💬"}</button>

        <div className={`chat-interface ${chatOpen ? "chat-open" : "chat-closed"}`}>
          <div className={`sidebar ${sidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
            <div style={{ background: "#2563eb", color: "white", padding: "16px", minWidth: "280px" }}>
              <button onClick={createNewSession} style={{ width: "100%", padding: "12px", background: "#1d4ed8", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "14px", fontWeight: "500" }}>✨ New Chat</button>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: "8px", minWidth: "280px" }}>
              {sessions.map((s) => (
                <div key={s.id} onClick={() => setCurrentSessionId(s.id)} style={{ padding: "12px", marginBottom: "8px", borderRadius: "8px", cursor: "pointer", background: s.id === currentSessionId ? "#eff6ff" : "transparent", border: s.id === currentSessionId ? "1px solid #3b82f6" : "1px solid transparent" }}>
                  <div style={{ fontSize: "14px", fontWeight: s.id === currentSessionId ? "bold" : "normal", color: "#1f2937", marginBottom: "4px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.name}</div>
                  <div style={{ fontSize: "12px", color: "#6b7280" }}>{formatDate(s.createdAt)}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, background: "white", display: "flex", flexDirection: "column", height: "100vh" }}>
            <div style={{ background: "#2563eb", color: "white", padding: "16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <button onClick={() => setSidebarOpen(!sidebarOpen)} style={{ padding: "8px", background: "transparent", border: "none", color: "white", cursor: "pointer", fontSize: "18px" }}>☰</button>
                <div>
                  <h1 style={{ fontSize: "18px", fontWeight: "600", margin: 0 }}>INGRO Assistant</h1>
                  <p style={{ fontSize: "12px", color: "#bfdbfe", margin: 0 }}>Groundwater Resources</p>
                </div>
              </div>
              <button onClick={() => setChatOpen(false)} style={{ padding: "8px", background: "transparent", border: "none", color: "white", cursor: "pointer", fontSize: "18px" }}>✕</button>
            </div>

            <div style={{ background: "#eff6ff", padding: "16px", borderBottom: "1px solid #e5e7eb", textAlign: "center" }}>
              <div style={{ fontWeight: "600", color: "#1e40af", fontSize: "16px" }}>Welcome to INGRO</div>
              <div style={{ color: "#2563eb", fontSize: "12px", marginTop: "4px" }}>Your AI assistant for groundwater resources</div>
            </div>

            <div style={{ padding: "12px 16px", background: "#f9fafb", borderBottom: "1px solid #e5e7eb" }}>
              <div style={{ fontSize: "12px", color: "#6b7280", marginBottom: "8px", fontWeight: "500" }}>Select Mode:</div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {[
                  { value: "normal", label: "💬 Normal Query" },
                  { value: "pdf", label: "📄 PDF Analysis" },
                  { value: "borewell", label: "🗺️ Borewell Report" },
                ].map((m) => (
                  <button key={m.value} onClick={() => { setCurrentMode(m.value); setSelectedFile(null); setLatitude(""); setLongitude(""); if (fileInputRef.current) fileInputRef.current.value = ""; }} style={{ padding: "8px 16px", borderRadius: "8px", border: currentMode === m.value ? "2px solid #2563eb" : "1px solid #d1d5db", background: currentMode === m.value ? "#eff6ff" : "white", color: currentMode === m.value ? "#1e40af" : "#4b5563", fontSize: "13px", fontWeight: currentMode === m.value ? "600" : "500", cursor: "pointer" }}>{m.label}</button>
                ))}
              </div>
            </div>

            <div style={{ flex: 1, overflowY: "auto", padding: "16px", background: "#f9fafb" }}>
              {currentSession?.messages.length === 0 ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: "20px", color: "#6b7280", textAlign: "center" }}>
                  <div style={{ fontSize: "48px", marginBottom: "16px" }}>🌊</div>
                  <p style={{ marginBottom: "24px", fontSize: "14px", fontWeight: "500" }}>Ask me anything about groundwater resources</p>
                </div>
              ) : (
                currentSession?.messages.map((msg) => (
                  <div key={msg.id} className="msg-anim" style={{ display: "flex", flexDirection: "column", marginBottom: "20px", alignItems: msg.sender === "user" ? "flex-end" : "flex-start" }}>
                    <div style={{ maxWidth: "90%", padding: "16px", borderRadius: "16px", boxShadow: "0 2px 12px rgba(0,0,0,0.1)", background: msg.sender === "user" ? "#2563eb" : "white", color: msg.sender === "user" ? "white" : "#1f2937", border: msg.sender === "bot" ? "1px solid #e5e7eb" : "none" }}>
                      <div style={{ fontSize: "14px", lineHeight: "1.6", whiteSpace: "pre-wrap" }}>{msg.text}</div>
                      {msg.reportUrl && (
                        <div style={{ marginTop: "16px" }}>
                          <a href={msg.reportUrl} target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "linear-gradient(135deg, #10b981, #059669)", color: "white", padding: "12px 20px", borderRadius: "10px", textDecoration: "none", fontSize: "14px", fontWeight: "600", boxShadow: "0 4px 12px rgba(16, 185, 129, 0.3)" }}>📊 View Report</a>
                        </div>
                      )}
                      <div style={{ fontSize: "12px", opacity: 0.7, textAlign: "right", color: msg.sender === "user" ? "#bfdbfe" : "#6b7280", marginTop: "8px" }}>{formatTime(msg.timestamp)}</div>
                    </div>
                  </div>
                ))
              )}
              {isLoading && (
                <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "16px" }}>
                  <div style={{ background: "white", border: "1px solid #e5e7eb", padding: "16px", borderRadius: "16px", boxShadow: "0 2px 8px rgba(0,0,0,0.1)" }}>
                    <div className="loading-dots">
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                      <div className="loading-dot"></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div style={{ padding: "16px", background: "white", borderTop: "1px solid #e5e7eb" }}>
              {currentMode === "normal" && (
                <div style={{ display: "flex", alignItems: "flex-end", gap: "12px" }}>
                  <textarea value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }} placeholder="Ask about groundwater..." disabled={isLoading} style={{ flex: 1, padding: "12px 16px", border: "2px solid #d1d5db", borderRadius: "16px", resize: "none", outline: "none", fontSize: "14px", minHeight: "48px", maxHeight: "120px", opacity: isLoading ? 0.5 : 1 }} rows={1} />
                  <button onClick={handleSendMessage} disabled={inputValue.trim() === "" || isLoading} style={{ padding: "12px 16px", borderRadius: "16px", border: "none", cursor: inputValue.trim() === "" || isLoading ? "not-allowed" : "pointer", background: inputValue.trim() === "" || isLoading ? "#d1d5db" : "#2563eb", color: inputValue.trim() === "" || isLoading ? "#6b7280" : "white", fontWeight: "600", fontSize: "14px" }}>{isLoading ? "..." : "Send ➤"}</button>
                </div>
              )}
              {currentMode === "pdf" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileSelect} disabled={isLoading} style={{ display: "none" }} />
                    <button onClick={() => fileInputRef.current?.click()} disabled={isLoading} style={{ flex: 1, padding: "12px", border: "2px dashed #2563eb", borderRadius: "12px", background: "#eff6ff", color: "#1e40af", fontSize: "14px", fontWeight: "500", cursor: isLoading ? "not-allowed" : "pointer" }}>{selectedFile ? `📄 ${selectedFile.name}` : "📄 Choose PDF"}</button>
                    <button onClick={handleSendMessage} disabled={!selectedFile || isLoading} style={{ padding: "12px 16px", borderRadius: "16px", border: "none", cursor: !selectedFile || isLoading ? "not-allowed" : "pointer", background: !selectedFile || isLoading ? "#d1d5db" : "#2563eb", color: !selectedFile || isLoading ? "#6b7280" : "white", fontWeight: "600", fontSize: "14px" }}>Analyze</button>
                  </div>
                  {uploadProgress > 0 && <div style={{ width: "100%", background: "#e5e7eb", borderRadius: "4px", height: "4px" }}><div style={{ width: `${uploadProgress}%`, background: "#2563eb", height: "100%", borderRadius: "4px" }} /></div>}
                </div>
              )}
              {currentMode === "borewell" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <input type="text" value={latitude} onChange={(e) => setLatitude(e.target.value)} placeholder="Latitude" disabled={isLoading} style={{ flex: 1, padding: "12px", border: "2px solid #d1d5db", borderRadius: "12px", fontSize: "14px" }} />
                    <input type="text" value={longitude} onChange={(e) => setLongitude(e.target.value)} placeholder="Longitude" disabled={isLoading} style={{ flex: 1, padding: "12px", border: "2px solid #d1d5db", borderRadius: "12px", fontSize: "14px" }} />
                  </div>
                  <button onClick={handleSendMessage} disabled={!latitude || !longitude || isLoading} style={{ padding: "12px", borderRadius: "16px", border: "none", cursor: !latitude || !longitude || isLoading ? "not-allowed" : "pointer", background: !latitude || !longitude || isLoading ? "#d1d5db" : "#2563eb", color: !latitude || !longitude || isLoading ? "#6b7280" : "white", fontWeight: "600", fontSize: "14px" }}>{isLoading ? "Analyzing..." : "Get Report"}</button>
                </div>
              )}
            </div>
          </div>
        </div>

        {chatOpen && <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 30 }} onClick={() => setChatOpen(false)} />}
      </div>
    </>
  );
};

export default ChatbotInterface;