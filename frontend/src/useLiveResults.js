import { useEffect, useRef, useState } from "react";
import { api } from "./api";

/** Loads results once over REST, then keeps them fresh over a WebSocket. */
export default function useLiveResults() {
  const [results, setResults] = useState([]);
  const [stats, setStats] = useState(null);
  const [connected, setConnected] = useState(false);
  const retry = useRef(null);

  useEffect(() => {
    let socket;
    let closed = false;

    api("/results/").then(setResults).catch(() => {});
    api("/results/stats/").then(setStats).catch(() => {});

    const connect = () => {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${proto}://${window.location.host}/ws/results/`);
      socket.onopen = () => setConnected(true);
      socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        setResults(data.results);
        setStats(data.stats);
      };
      socket.onclose = () => {
        setConnected(false);
        if (!closed) retry.current = setTimeout(connect, 2000);
      };
    };
    connect();

    return () => {
      closed = true;
      clearTimeout(retry.current);
      socket && socket.close();
    };
  }, []);

  return { results, stats, connected };
}
