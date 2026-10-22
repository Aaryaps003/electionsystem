import { useCallback, useEffect, useMemo, useState } from "react";
import { api, downloadResultsXml } from "../api";
import { useAuth } from "../auth.jsx";

const ALPHABET = "abcdefghjkmnpqrstuvwxyzACDEFGHJKLMNPQRTUVWXY346789";
function generatePassword(len = 8) {
  const a = new Uint32Array(len);
  crypto.getRandomValues(a);
  return Array.from(a, (n) => ALPHABET[n % ALPHABET.length]).join("");
}

function VoterForm({ onAdded, onAuthError }) {
  const blank = { name: "", prn: "", cls: "", division: "", username: "", password: "" };
  const [form, setForm] = useState(blank);
  const [msg, setMsg] = useState(null);
  const [created, setCreated] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setMsg(null); setCreated(null);
    const body = { ...form, username: form.username.trim() || form.prn.trim() };
    try {
      await api("/admin/addVoter/", { method: "POST", body, auth: "admin" });
      setCreated({ name: form.name, username: body.username.toLowerCase(), password: form.password });
      setForm(blank);
      onAdded();
    } catch (err) {
      onAuthError(err);
      setMsg(err.message);
    }
  };

  return (
    <form className="panel panel-title h-100" onSubmit={submit}>
      <h3 className="h5 mb-3">Add voter</h3>
      <div className="row g-2 mb-2">
        <div className="col-12"><input className="form-control" placeholder="Full name" value={form.name} onChange={set("name")} required /></div>
        <div className="col-12"><input className="form-control" placeholder="PRN" value={form.prn} onChange={set("prn")} required /></div>
        <div className="col-7"><input className="form-control" placeholder="Class (e.g. SY-CSE)" value={form.cls} onChange={set("cls")} required /></div>
        <div className="col-5"><input className="form-control" placeholder="Division" value={form.division} onChange={set("division")} required /></div>
        <div className="col-12"><input className="form-control" placeholder="Username (defaults to PRN)" value={form.username} onChange={set("username")} autoComplete="off" /></div>
        <div className="col-12">
          <div className="input-group">
            <input className="form-control" placeholder="Password (min 6)" value={form.password} onChange={set("password")} minLength={6} required autoComplete="new-password" />
            <button type="button" className="btn btn-outline-secondary" onClick={() => setForm({ ...form, password: generatePassword() })}>Generate</button>
          </div>
        </div>
      </div>
      {msg && <div className="alert alert-danger py-2">{msg}</div>}
      {created && (
        <div className="cred-box mb-3">
          <div className="small mb-1">Voter added. Give these to {created.name} now; the password can't be shown again.</div>
          <div>Username: <code>{created.username}</code> · Password: <code>{created.password}</code></div>
          <button type="button" className="btn btn-sm btn-outline-primary mt-2"
            onClick={() => navigator.clipboard.writeText(`Username: ${created.username}\nPassword: ${created.password}`)}>Copy</button>
        </div>
      )}
      <button className="btn btn-primary">Add voter</button>
    </form>
  );
}

function CandidateForm({ onAuthError }) {
  const blank = { prn: "", name: "", cls: "", division: "" };
  const [form, setForm] = useState(blank);
  const [msg, setMsg] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      await api("/admin/addCandidate/", { method: "POST", body: form, auth: "admin" });
      setMsg({ ok: true, text: "Candidate added. A NOTA option now exists for this division." });
      setForm(blank);
    } catch (err) {
      onAuthError(err);
      setMsg({ ok: false, text: err.message });
    }
  };

  return (
    <form className="panel panel-title h-100" onSubmit={submit}>
      <h3 className="h5 mb-3">Add candidate</h3>
      <div className="row g-2 mb-3">
        <div className="col-12"><input className="form-control" placeholder="Full name" value={form.name} onChange={set("name")} required /></div>
        <div className="col-12"><input className="form-control" placeholder="PRN" value={form.prn} onChange={set("prn")} required /></div>
        <div className="col-7"><input className="form-control" placeholder="Class (e.g. SY-CSE)" value={form.cls} onChange={set("cls")} required /></div>
        <div className="col-5"><input className="form-control" placeholder="Division" value={form.division} onChange={set("division")} required /></div>
      </div>
      {msg && <div className={`alert ${msg.ok ? "alert-success" : "alert-danger"} py-2`}>{msg.text}</div>}
      <button className="btn btn-primary">Add candidate</button>
    </form>
  );
}

export default function Admin() {
  const { logout } = useAuth();
  const [voters, setVoters] = useState([]);
  const [query, setQuery] = useState("");
  const [exportError, setExportError] = useState("");
  const [notice, setNotice] = useState("");

  const onAuthError = (err) => { if (err.status === 401 || err.status === 403) logout(); };

  const loadVoters = useCallback(() => {
    api("/admin/voters/", { auth: "admin" }).then(setVoters).catch(onAuthError);
  }, []); // eslint-disable-line

  useEffect(loadVoters, [loadVoters]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return voters;
    return voters.filter((v) => [v.name, v.prn, v.username, v.cls].some((x) => (x || "").toLowerCase().includes(q)));
  }, [voters, query]);

  const exportXml = async () => {
    setExportError("");
    try { await downloadResultsXml(); }
    catch (err) { onAuthError(err); setExportError(err.message); }
  };

  const resetPassword = async (v) => {
    const suggestion = generatePassword();
    const pw = window.prompt(`New password for ${v.name} (min 6 characters):`, suggestion);
    if (!pw) return;
    try {
      await api("/admin/resetPassword/", { method: "POST", body: { prn: v.prn, password: pw }, auth: "admin" });
      setNotice(`Password for ${v.name} updated. New password: ${pw}`);
    } catch (err) { onAuthError(err); setNotice(err.message); }
  };

  const voted = voters.filter((v) => v.hasVoted).length;

  return (
    <>
      <div className="panel page-head d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <h2 className="page-title mb-0">Election admin</h2>
        <button className="btn btn-outline-primary" onClick={exportXml}>Export results (XML)</button>
      </div>
      {exportError && <div className="alert alert-danger">{exportError}</div>}

      <div className="row g-3 mb-3">
        <div className="col-6 col-md-3"><div className="stat-chip"><b>{voters.length}</b>registered voters</div></div>
        <div className="col-6 col-md-3"><div className="stat-chip"><b>{voted}</b>have voted</div></div>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-lg-6"><VoterForm onAdded={loadVoters} onAuthError={onAuthError} /></div>
        <div className="col-lg-6"><CandidateForm onAuthError={onAuthError} /></div>
      </div>

      <div className="panel">
        <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
          <h3 className="h5 mb-0">Voters</h3>
          <input className="form-control" style={{ maxWidth: 260 }} placeholder="Search name, PRN, username" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        {notice && <div className="cred-box mb-3">{notice}</div>}
        <div className="table-responsive">
          <table className="table align-middle mb-0">
            <thead><tr><th>Name</th><th>PRN</th><th>Class</th><th>Username</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {filtered.length === 0 && <tr><td colSpan="6" className="text-secondary">No voters found. Add one above.</td></tr>}
              {filtered.map((v) => (
                <tr key={v.prn}>
                  <td>{v.name}</td>
                  <td>{v.prn}</td>
                  <td>{v.cls} · {v.division}</td>
                  <td>{v.username || "—"}</td>
                  <td><span className={`pill ${v.hasVoted ? "voted" : "pending"}`}>{v.hasVoted ? "Voted" : "Not voted"}</span></td>
                  <td className="text-end"><button className="btn btn-sm btn-outline-primary" onClick={() => resetPassword(v)}>Reset password</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
