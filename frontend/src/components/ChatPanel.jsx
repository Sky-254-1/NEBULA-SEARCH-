export function ChatPanel({ messages, loading, onClear }) {
  if (!messages.length && !loading) return null;

  return (
    <section className="chat-panel" aria-label="Conversation history">
      <div className="chat-header">
        <h2>Conversation</h2>
        {messages.length > 0 && (
          <button type="button" className="btn ghost" onClick={onClear}>
            Clear
          </button>
        )}
      </div>
      {loading ? (
        <p className="muted">Loading chat…</p>
      ) : (
        <ul className="chat-messages">
          {messages.map((msg, i) => (
            <li key={i} className={`chat-msg chat-msg--${msg.role}`}>
              <span className="chat-role">{msg.role}</span>
              <p>{msg.content}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
