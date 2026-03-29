import { useEffect, useRef, useState } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const ROLE_OPTIONS = ["employee", "manager", "hr", "finance", "legal", "admin"];
const DEMO_USERS = [
  "alice / employee123",
  "maya / manager123",
  "harper / hr123",
  "frank / finance123",
  "lara / legal123",
  "admin / admin123",
];

function authHeaders(token) {
  return token ? { "X-Auth-Token": token } : {};
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const base64 = result.includes(",") ? result.split(",")[1] : result;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [auth, setAuth] = useState({ token: "", user: null });
  const [loginError, setLoginError] = useState("");
  const [uploadForm, setUploadForm] = useState({
    title: "",
    department: "general",
    classification: "internal",
    allowed_roles: ["employee"],
    summary: "",
  });
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [auditLogs, setAuditLogs] = useState([]);
  const chatEndRef = useRef(null);

  useEffect(() => {
    const savedToken = localStorage.getItem("devsearch_token");
    if (!savedToken) return;

    axios
      .get(`${API_BASE}/auth/me`, { headers: authHeaders(savedToken) })
      .then((res) => {
        if (res.data.status === "success") {
          setAuth({ token: savedToken, user: res.data.user });
        } else {
          localStorage.removeItem("devsearch_token");
        }
      })
      .catch(() => {
        localStorage.removeItem("devsearch_token");
      });
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (auth.user?.role === "admin") {
      fetchAuditLogs();
    }
  }, [auth.user]);

  const fetchAuditLogs = async () => {
    try {
      const res = await axios.get(`${API_BASE}/admin/audit-logs`, {
        headers: authHeaders(auth.token),
      });
      if (res.data.status === "success") {
        setAuditLogs(res.data.logs || []);
      }
    } catch (err) {
      console.error("Audit log fetch failed", err);
    }
  };

  const handleLogin = async () => {
    setLoginError("");
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, loginForm);
      if (res.data.status !== "success") {
        setLoginError(res.data.error || "Login failed.");
        return;
      }

      localStorage.setItem("devsearch_token", res.data.token);
      setAuth({ token: res.data.token, user: res.data.user });
      setMessages([]);
      setLoginForm({ username: "", password: "" });
    } catch (err) {
      console.error("Login failed", err);
      setLoginError("Login request failed.");
    }
  };

  const handleLogout = async () => {
    try {
      await axios.post(
        `${API_BASE}/auth/logout`,
        {},
        { headers: authHeaders(auth.token) }
      );
    } catch (err) {
      console.error("Logout failed", err);
    }

    localStorage.removeItem("devsearch_token");
    setAuth({ token: "", user: null });
    setMessages([]);
    setAuditLogs([]);
  };

  const sendQuery = async () => {
    if (!query.trim() || !auth.user) return;

    const userText = query;
    setMessages((prev) => [
      ...prev,
      { role: "user", text: userText, userRole: auth.user.role, username: auth.user.username },
    ]);
    setQuery("");
    setLoading(true);

    try {
      const res = await axios.post(
        `${API_BASE}/chat`,
        { query: userText },
        { headers: authHeaders(auth.token) }
      );

      const status = res.data.status || (res.data.error ? "error" : "success");
      const answerText =
        status === "error"
          ? res.data.error || "Server error."
          : res.data.answer || "No response received";

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: answerText,
          status,
          grounded: Boolean(res.data.grounded),
          sources: res.data.sources || [],
          userRole: auth.user.role,
          username: auth.user.username,
        },
      ]);
    } catch (err) {
      console.error("API Error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: "Error fetching response.",
          status: "error",
          grounded: false,
          sources: [],
          userRole: auth.user.role,
          username: auth.user.username,
        },
      ]);
    }

    setLoading(false);
    if (auth.user.role === "admin") {
      fetchAuditLogs();
    }
  };

  const resetChat = () => {
    setMessages([]);
    setQuery("");
  };

  const toggleAllowedRole = (role) => {
    setUploadForm((prev) => ({
      ...prev,
      allowed_roles: prev.allowed_roles.includes(role)
        ? prev.allowed_roles.filter((item) => item !== role)
        : [...prev.allowed_roles, role],
    }));
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      setUploadMessage("Choose a file to upload.");
      return;
    }

    try {
      const content_base64 = await fileToBase64(uploadFile);
      const res = await axios.post(
        `${API_BASE}/admin/upload`,
        {
          filename: uploadFile.name,
          content_base64,
          ...uploadForm,
        },
        { headers: authHeaders(auth.token) }
      );

      setUploadMessage(res.data.message || res.data.error || "Upload finished.");
      if (res.data.status === "success") {
        setUploadFile(null);
        setUploadForm({
          title: "",
          department: "general",
          classification: "internal",
          allowed_roles: ["employee"],
          summary: "",
        });
        fetchAuditLogs();
      }
    } catch (err) {
      console.error("Upload failed", err);
      setUploadMessage("Upload failed.");
    }
  };

  if (!auth.user) {
    return (
      <div className="min-h-screen bg-[#15161c] text-white flex items-center justify-center p-6">
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-[1.2fr_0.8fr] gap-6">
          <div className="rounded-3xl border border-gray-800 bg-[radial-gradient(circle_at_top_left,_rgba(66,153,225,0.24),_transparent_40%),_#20232b] p-8">
            <div className="text-sm uppercase tracking-[0.3em] text-cyan-300">DevSearch AI</div>
            <h1 className="mt-4 text-4xl font-bold leading-tight">
              Local company knowledge retrieval with role-based access.
            </h1>
            <p className="mt-4 text-gray-300 max-w-2xl">
              Sign in as a local company user, query authorized internal documents,
              upload new materials as admin, and keep audit trails on-device.
            </p>

            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div className="rounded-2xl bg-[#171a20] p-4 border border-gray-800">
                <div className="font-semibold">Capabilities</div>
                <div className="mt-2 text-gray-400">
                  Local-only search, RBAC-aware answers, audit logs, and admin uploads.
                </div>
              </div>
              <div className="rounded-2xl bg-[#171a20] p-4 border border-gray-800">
                <div className="font-semibold">Supported docs</div>
                <div className="mt-2 text-gray-400">
                  TXT, MD, CSV, JSON, code files, and optional PDF or DOCX parsing.
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-gray-800 bg-[#1c1f27] p-8">
            <h2 className="text-2xl font-semibold">Sign in</h2>
            <p className="mt-2 text-sm text-gray-400">
              Demo local accounts
            </p>
            <div className="mt-3 rounded-2xl bg-[#14161b] p-4 text-xs text-gray-300 space-y-1">
              {DEMO_USERS.map((user) => (
                <div key={user}>{user}</div>
              ))}
            </div>

            <div className="mt-6 space-y-4">
              <input
                value={loginForm.username}
                onChange={(e) => setLoginForm((prev) => ({ ...prev, username: e.target.value }))}
                placeholder="Username"
                className="w-full rounded-xl bg-[#11131a] border border-gray-800 px-4 py-3 outline-none"
              />
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm((prev) => ({ ...prev, password: e.target.value }))}
                placeholder="Password"
                className="w-full rounded-xl bg-[#11131a] border border-gray-800 px-4 py-3 outline-none"
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              />
              {loginError && (
                <div className="rounded-xl border border-red-700 bg-[#3a2020] px-4 py-3 text-sm text-red-100">
                  {loginError}
                </div>
              )}
              <button
                onClick={handleLogin}
                className="w-full rounded-xl bg-cyan-600 px-4 py-3 font-semibold hover:bg-cyan-500"
              >
                Enter workspace
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#15161c] text-white">
      <div className="w-96 bg-[#20232b] p-5 flex flex-col justify-between border-r border-gray-800">
        <div className="space-y-5">
          <div className="rounded-2xl bg-[#171a20] p-4 border border-gray-800">
            <div className="text-xs uppercase tracking-[0.2em] text-cyan-300">
              Logged in
            </div>
            <h1 className="mt-2 text-2xl font-bold">DevSearch AI</h1>
            <div className="mt-3 text-sm text-gray-300">
              {auth.user.name} · {auth.user.role}
            </div>
            <div className="text-xs text-gray-400">@{auth.user.username}</div>
            <button
              onClick={handleLogout}
              className="mt-4 rounded-lg bg-gray-700 px-3 py-2 text-sm hover:bg-gray-600"
            >
              Log out
            </button>
          </div>

          <button
            onClick={resetChat}
            className="w-full bg-gray-700 px-3 py-2 rounded hover:bg-gray-600"
          >
            + New Search
          </button>

          <div className="rounded-lg bg-[#2a2c34] p-4 text-sm text-gray-300 space-y-2">
            <p>Indexed mode: company documents</p>
            <p>Current access: {auth.user.role}</p>
            <p>Documents are filtered by authenticated role before answer generation.</p>
          </div>

          {auth.user.role === "admin" && (
            <div className="rounded-2xl bg-[#171a20] p-4 border border-gray-800 space-y-3">
              <div className="font-semibold">Admin Upload</div>
              <input
                type="file"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="w-full text-sm text-gray-300"
              />
              <input
                value={uploadForm.title}
                onChange={(e) => setUploadForm((prev) => ({ ...prev, title: e.target.value }))}
                placeholder="Document title"
                className="w-full rounded bg-[#11131a] border border-gray-800 px-3 py-2 text-sm outline-none"
              />
              <input
                value={uploadForm.department}
                onChange={(e) => setUploadForm((prev) => ({ ...prev, department: e.target.value }))}
                placeholder="Department"
                className="w-full rounded bg-[#11131a] border border-gray-800 px-3 py-2 text-sm outline-none"
              />
              <select
                value={uploadForm.classification}
                onChange={(e) => setUploadForm((prev) => ({ ...prev, classification: e.target.value }))}
                className="w-full rounded bg-[#11131a] border border-gray-800 px-3 py-2 text-sm outline-none"
              >
                <option value="internal">internal</option>
                <option value="restricted">restricted</option>
                <option value="confidential">confidential</option>
              </select>
              <textarea
                value={uploadForm.summary}
                onChange={(e) => setUploadForm((prev) => ({ ...prev, summary: e.target.value }))}
                placeholder="Summary"
                className="w-full rounded bg-[#11131a] border border-gray-800 px-3 py-2 text-sm outline-none min-h-20"
              />
              <div>
                <div className="text-xs uppercase tracking-wide text-gray-400 mb-2">
                  Allowed roles
                </div>
                <div className="flex flex-wrap gap-2">
                  {ROLE_OPTIONS.map((role) => (
                    <button
                      key={role}
                      type="button"
                      onClick={() => toggleAllowedRole(role)}
                      className={`rounded-full px-3 py-1 text-xs border ${
                        uploadForm.allowed_roles.includes(role)
                          ? "bg-cyan-600 border-cyan-500"
                          : "bg-[#11131a] border-gray-700"
                      }`}
                    >
                      {role}
                    </button>
                  ))}
                </div>
              </div>
              <button
                onClick={handleUpload}
                className="w-full rounded-lg bg-cyan-600 px-3 py-2 text-sm font-semibold hover:bg-cyan-500"
              >
                Upload and re-index
              </button>
              {uploadMessage && (
                <div className="rounded-lg bg-[#11131a] px-3 py-2 text-sm text-gray-300">
                  {uploadMessage}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="rounded-lg bg-[#17181d] p-4 text-xs text-gray-400 space-y-2">
          <p>Try:</p>
          <p>"What does the leave policy say?"</p>
          <p>"What is the engineering API overview?"</p>
          <p>"Show the expense reimbursement rule."</p>
        </div>
      </div>

      <div className="flex flex-col flex-1">
        <div className="border-b border-gray-700 px-6 py-3 text-sm text-gray-300">
          Local-only retrieval. Grounded answers use only documents accessible to the authenticated role.
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[1fr_340px] min-h-0 flex-1">
          <div className="flex flex-col min-h-0">
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className="space-y-2">
                  <div
                    className={`p-4 rounded-lg max-w-4xl ${
                      msg.role === "user" ? "bg-[#0b93f6] ml-auto" : "bg-[#444654]"
                    }`}
                  >
                    <div className="text-xs uppercase tracking-wide mb-2 opacity-75">
                      {msg.role === "user"
                        ? `User • ${msg.userRole}`
                        : `Assistant • ${msg.userRole}`}
                    </div>
                    <div>{msg.text}</div>
                  </div>

                  {msg.role === "bot" && msg.status === "error" && (
                    <div className="max-w-4xl rounded-lg border border-red-700 bg-[#3a2020] px-4 py-3 text-sm text-red-100">
                      Server error while processing this query. {msg.text}
                    </div>
                  )}

                  {msg.role === "bot" && msg.status !== "error" && !msg.grounded && (
                    <div className="max-w-4xl rounded-lg border border-amber-700 bg-[#3a3120] px-4 py-3 text-sm text-amber-100">
                      No authorized supporting document was strong enough to answer this query.
                    </div>
                  )}

                  {msg.role === "bot" && msg.sources?.length > 0 && (
                    <div className="max-w-4xl bg-[#2d2f39] border border-gray-700 rounded-lg p-3 text-sm text-gray-200">
                      <div className="font-semibold mb-2">Authorized Sources</div>
                      <div className="space-y-2">
                        {msg.sources.map((source, idx) => (
                          <div key={idx} className="bg-[#23252d] rounded p-3">
                            <div className="font-medium">{source.title}</div>
                            {source.name && source.name !== source.title && (
                              <div className="text-gray-300">{source.name}</div>
                            )}
                            <div className="text-gray-400">
                              {source.document_type} • {source.department} • {source.classification}
                            </div>
                            <div className="text-gray-400">{source.path}</div>
                            <div className="text-gray-400">score: {source.score}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="bg-[#444654] p-4 rounded-lg w-fit">
                  Searching authorized company documents...
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            <div className="p-4 border-t border-gray-700 flex items-center gap-3">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about internal company documents..."
                className="flex-1 p-3 rounded bg-[#40414f] outline-none"
                onKeyDown={(e) => e.key === "Enter" && sendQuery()}
              />
              <button
                onClick={sendQuery}
                className="bg-green-600 px-5 py-2 rounded hover:bg-green-500"
              >
                Search
              </button>
            </div>
          </div>

          <div className="border-l border-gray-800 bg-[#17181d] p-5 space-y-4 overflow-y-auto">
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-cyan-300">
                Session
              </div>
              <div className="mt-2 text-sm text-gray-300">
                Signed in as <span className="font-semibold">{auth.user.name}</span>
              </div>
              <div className="text-sm text-gray-400">
                Role: {auth.user.role}
              </div>
            </div>

            <div className="rounded-2xl bg-[#20232b] p-4 border border-gray-800">
              <div className="font-semibold">Security model</div>
              <div className="mt-2 text-sm text-gray-400">
                Answers are generated only from documents allowed for the authenticated role.
              </div>
            </div>

            {auth.user.role === "admin" && (
              <div className="rounded-2xl bg-[#20232b] p-4 border border-gray-800">
                <div className="flex items-center justify-between">
                  <div className="font-semibold">Recent audit log</div>
                  <button
                    onClick={fetchAuditLogs}
                    className="text-xs text-cyan-300 hover:text-cyan-200"
                  >
                    Refresh
                  </button>
                </div>
                <div className="mt-3 space-y-3 text-xs">
                  {auditLogs.length === 0 && (
                    <div className="text-gray-500">No audit events yet.</div>
                  )}
                  {auditLogs.map((entry, idx) => (
                    <div key={`${entry.timestamp}-${idx}`} className="rounded-xl bg-[#11131a] p-3 border border-gray-800">
                      <div className="text-gray-200">
                        {entry.action} · {entry.status}
                      </div>
                      <div className="text-gray-500">
                        {entry.username || "anonymous"} · {entry.role || "none"}
                      </div>
                      <div className="text-gray-500">{entry.timestamp}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
