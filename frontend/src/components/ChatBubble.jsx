import { useState } from "react";
import { motion } from "framer-motion";
import { Check, Copy, CircleAlert } from "lucide-react";
import TracePanel from "./TracePanel";
import Tooltip from "./Tooltip";
import Avatar from "./Avatar";
import { AgentIcon } from "../lib/icons";
import { Markdown } from "../lib/markdown";
import { fmtLatency, fmtNumber } from "../lib/format";
import { useSession } from "../context/SessionContext";

export default function ChatBubble({ message, agentIcon }) {
  const { currentUser } = useSession();
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";
  const tokens = (message.prompt_tokens || 0) + (message.completion_tokens || 0);

  const copy = () => {
    navigator.clipboard?.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (isUser) {
    return (
      <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end gap-3">
        <div className="max-w-[78%] rounded-2xl rounded-tr-md bg-ink-950 px-4 py-2.5 text-[14px] leading-relaxed text-white">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <Avatar name={currentUser?.name} role={currentUser?.role} size="sm" />
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="group flex gap-3">
      <AgentIcon name={agentIcon} size="sm" tone="dark" />
      <div className="min-w-0 max-w-[85%] flex-1">
        {message.error ? (
          <div className="flex items-start gap-2 rounded-2xl rounded-tl-md border border-red-100 bg-red-50 px-4 py-3 text-[13.5px] text-red-700">
            <CircleAlert size={15} className="mt-0.5 shrink-0" /> {message.content}
          </div>
        ) : (
          <div className="text-[14px] leading-relaxed text-ink-950">
            <Markdown text={message.content} />
          </div>
        )}
        {!message.error && (
          <div className="mt-1.5 flex items-center gap-3 text-[11.5px] text-mist-400">
            {message.latency_ms != null && message.latency_ms > 0 && (
              <span className="font-mono">
                {fmtLatency(message.latency_ms)}
                {tokens > 0 && ` · ${fmtNumber(tokens)} tokens`}
              </span>
            )}
            <Tooltip label={copied ? "Copiado" : "Copiar respuesta"}>
              <button onClick={copy} className="focus-ring rounded p-0.5 opacity-0 transition hover:text-ink-950 group-hover:opacity-100">
                {copied ? <Check size={13} /> : <Copy size={13} />}
              </button>
            </Tooltip>
          </div>
        )}
        {message.trace?.length > 0 && <TracePanel trace={message.trace} />}
      </div>
    </motion.div>
  );
}
