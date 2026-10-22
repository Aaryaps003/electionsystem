import useLiveResults from "../useLiveResults";

export default function Results() {
  const { results, stats, connected } = useLiveResults();

  const groups = {};
  results.forEach((c) => {
    const key = `${c.cls}|${c.division}`;
    (groups[key] ||= { cls: c.cls, division: c.division, items: [] }).items.push(c);
  });
  const divInfo = (cls, division) =>
    stats?.divisions.find((d) => d.cls === cls && d.division === division);

  return (
    <>
      <div className="panel page-head d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <h2 className="page-title mb-0">Live results</h2>
        <span className="text-secondary small">
          <span className={`live-dot ${connected ? "on" : ""}`} />
          {connected ? "Updating live" : "Reconnecting…"}
        </span>
      </div>

      {stats && (
        <div className="panel panel-title mb-4">
          <div className="stat-big">{stats.turnoutPercent}%</div>
          <div className="text-secondary mt-1">turnout · {stats.votesCast} of {stats.totalVoters} voters have voted</div>
          <div className="bar mt-3" role="progressbar" aria-valuenow={stats.turnoutPercent} aria-valuemin="0" aria-valuemax="100">
            <span style={{ width: `${stats.turnoutPercent}%` }} />
          </div>
        </div>
      )}

      {Object.values(groups).length === 0 && <div className="panel text-secondary">No candidates yet. Results will appear once the admin adds them.</div>}

      {Object.values(groups).map((g) => {
        const info = divInfo(g.cls, g.division);
        const total = g.items.reduce((s, c) => s + c.votes, 0);
        return (
          <section key={`${g.cls}${g.division}`} className="panel mb-4">
            <h3 className="h5 d-flex justify-content-between" style={{ color: "var(--wpu-navy)" }}>
              <span>{g.cls} · Division {g.division}</span>
              {info && <span className="text-secondary fs-6 fw-normal">{info.votesCast}/{info.totalVoters} voted</span>}
            </h3>
            <div className="d-grid gap-2">
              {g.items.map((c) => {
                const isLeader = info?.leaderPrn === c.prn;
                const pct = total ? (c.votes * 100) / total : 0;
                return (
                  <div key={c.prn} className={`result-row ${isLeader ? "leader" : ""}`}>
                    <div className="d-flex justify-content-between">
                      <strong>{c.name}{isLeader && <span className="leading-tag">Leading</span>}</strong>
                      <span>{c.votes} {c.votes === 1 ? "vote" : "votes"}</span>
                    </div>
                    <div className="bar mt-2"><span style={{ width: `${pct}%` }} /></div>
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}
    </>
  );
}
