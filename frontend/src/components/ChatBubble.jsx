import TracePanel from "./TracePanel";

export default function ChatBubble({ role, content, trace, latencyMs, agentEmoji }) {
  const isUser = role === "user";
  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-mist-100 text-[15px]">
        {isUser ? "🙂" : agentEmoji}
      </span>
      <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-[13.5px] leading-relaxed ${
            isUser ? "bg-ink-950 text-white" : "border border-mist-200 bg-white text-ink-950"
          }`}
        >
          <p className="whitespace-pre-wrap">{content}</p>
        </div>
        {!isUser && latencyMs != null && (
          <span className="mt-1 text-[10.5px] text-mist-400">{latencyMs} ms</span>
        )}
        {!isUser && trace?.length > 0 && (
          <div className="w-full min-w-[280px]">
            <TracePanel trace={trace} />
          </div>
        )}
      </div>
    </div>
  );
}
