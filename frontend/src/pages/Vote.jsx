import { useEffect, useState } from "react";
import { api, clearVoterToken, getVoterToken, setVoterToken } from "../api";

const STEPS = ["Sign in", "Choose", "Done"];

function Stepper({ index }) {
  return (
    <div className="stepper" aria-label="Voting progress">
      {STEPS.map((s, i) => (
        <div key={s} className={`s ${i < index ? "done" : ""} ${i === index ? "now" : ""}`}>{s}</div>
      ))}
    </div>
  );
}

export default function Vote() {
  // login | loading | ballot | confirm | done
  const [stage, setStage] = useState(getVoterToken() ? "loading" : "login");
  const [creds, setCreds] = useState({ username: "", password: "" });
  const [showPw, setShowPw] = useState(false);
  const [data, setData] = useState(null); // { voter, candidates }
  const [choice, setChoice] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const backToLogin = (message = "") => {
    clearVoterToken();
    setData(null); setChoice(null);
    setError(message);
    setStage("login");
  };

  const loadBallot = async () => {
    try {
      setData(await api("/voter/ballot/", { auth: "voter" }));
      setStage("ballot");
    } catch (err) {
      backToLogin(err.message);
    }
  };

  useEffect(() => { if (stage === "loading") loadBallot(); }, []); // eslint-disable-line

  const login = async (e) => {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      const res = await api("/voter/login/", { method: "POST", body: creds });
      setVoterToken(res.token);
      setCreds({ username: "", password: "" });
      await loadBallot();
    } catch (err) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  const submit = async () => {
    setError(""); setBusy(true);
    try {
      await api("/vote/", { method: "POST", body: { candidatePrn: choice }, auth: "voter" });
      clearVoterToken();
      setStage("done");
    } catch (err) {
      if (err.status === 401) backToLogin(err.message);
      else { setError(err.message); setStage("ballot"); }
    } finally { setBusy(false); }
  };

  if (stage === "loading") return <p className="text-white">Loading your ballot…</p>;

  if (stage === "done") {
    return (
      <div style={{ maxWidth: 560, margin: "0 auto" }}>
        <Stepper index={3} />
        <div className="panel panel-title text-center py-5">
          <h2 className="page-title">Your vote is in</h2>
          <p className="mb-3">Thank you, {data?.voter.name}. You've been signed out and can't vote again.</p>
          <a className="btn btn-primary" href="/results">View live results</a>
        </div>
      </div>
    );
  }

  if (stage === "ballot" || stage === "confirm") {
    const picked = data.candidates.find((c) => c.prn === choice);
    return (
      <div style={{ maxWidth: 680, margin: "0 auto" }}>
        <Stepper index={1} />
        <div className="panel page-head d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
          <div>
            <h2 className="page-title mb-1">{data.voter.cls} · Division {data.voter.division}</h2>
            <div className="text-secondary">Signed in as {data.voter.name} (PRN {data.voter.prn})</div>
          </div>
          <button className="btn btn-sm btn-outline-primary" onClick={() => backToLogin()}>Sign out</button>
        </div>

        {stage === "ballot" && (
          <>
            {data.candidates.length === 0 && <div className="alert alert-warning">No candidates have been added for your division yet.</div>}
            <div className="d-grid gap-2 mb-3">
              {data.candidates.map((c) => (
                <button key={c.prn} type="button" aria-pressed={choice === c.prn}
                  className={`ballot-row ${choice === c.prn ? "selected" : ""} ${c.isNota ? "nota" : ""}`}
                  onClick={() => setChoice(c.prn)}>
                  <span className="box" aria-hidden="true">✓</span>
                  <span><strong>{c.name}</strong>{!c.isNota && <span className="text-secondary"> · PRN {c.prn}</span>}</span>
                </button>
              ))}
            </div>
            {error && <div className="alert alert-danger">{error}</div>}
            <button className="btn btn-primary btn-lg" disabled={!choice} onClick={() => setStage("confirm")}>Review my choice</button>
          </>
        )}

        {stage === "confirm" && (
          <div className="panel panel-title">
            <h3 className="h5">Confirm your vote</h3>
            <p className="mb-1">You are voting for:</p>
            <p className="fs-4 fw-bold mb-3" style={{ color: "var(--wpu-navy)" }}>{picked?.name}</p>
            <p className="text-secondary">This can't be changed after you submit.</p>
            {error && <div className="alert alert-danger">{error}</div>}
            <div className="d-flex gap-2">
              <button className="btn btn-primary" disabled={busy} onClick={submit}>{busy ? "Submitting…" : "Submit vote"}</button>
              <button className="btn btn-outline-primary" disabled={busy} onClick={() => setStage("ballot")}>Change choice</button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 460, margin: "0 auto" }}>
      <Stepper index={0} />
      <form className="panel panel-title" onSubmit={login}>
        <h2 className="page-title mb-1">Voter sign in</h2>
        <p className="text-secondary">Use the credentials given to you by the election office.</p>
        <div className="mb-3">
          <label className="form-label" htmlFor="username">Username</label>
          <input id="username" className="form-control" autoComplete="username" autoFocus value={creds.username}
            onChange={(e) => setCreds({ ...creds, username: e.target.value })} required />
        </div>
        <div className="mb-3">
          <label className="form-label" htmlFor="password">Password</label>
          <div className="input-group">
            <input id="password" className="form-control" type={showPw ? "text" : "password"} autoComplete="current-password"
              value={creds.password} onChange={(e) => setCreds({ ...creds, password: e.target.value })} required />
            <button type="button" className="btn btn-outline-secondary" onClick={() => setShowPw(!showPw)}>{showPw ? "Hide" : "Show"}</button>
          </div>
        </div>
        {error && <div className="alert alert-danger">{error}</div>}
        <button className="btn btn-primary w-100 btn-lg" disabled={busy}>{busy ? "Signing in…" : "Sign in to vote"}</button>
      </form>
    </div>
  );
}
