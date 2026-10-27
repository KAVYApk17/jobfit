import { useQuery } from "@tanstack/react-query";
import { api } from "./api/client";

// Week 1 placeholder: proves the frontend can reach the API. Screens arrive in week 2.
export default function App() {
  const health = useQuery({ queryKey: ["health"], queryFn: () => api<{ status: string }>("/health") });

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: 32 }}>
      <h1>JobFit</h1>
      <p>
        API status:{" "}
        {health.isPending ? "checking…" : health.isError ? `unreachable (${health.error.message})` : health.data.status}
      </p>
      <p>
        API docs: <a href="http://localhost:8000/docs">localhost:8000/docs</a>
      </p>
    </main>
  );
}
