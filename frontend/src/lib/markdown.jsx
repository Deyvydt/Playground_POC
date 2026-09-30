// Renderizador mínimo de Markdown para respuestas de modelos: párrafos, listas,
// títulos, negrita, cursiva y código en línea. Construye elementos React (sin HTML crudo).

function inline(text, keyBase) {
  const parts = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)/g;
  let last = 0;
  let m;
  let i = 0;
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const tok = m[0];
    const key = `${keyBase}-${i++}`;
    if (tok.startsWith("**")) parts.push(<strong key={key}>{tok.slice(2, -2)}</strong>);
    else if (tok.startsWith("`")) parts.push(<code key={key}>{tok.slice(1, -1)}</code>);
    else parts.push(<em key={key}>{tok.slice(1, -1)}</em>);
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

export function Markdown({ text = "" }) {
  const lines = text.replace(/\r/g, "").split("\n");
  const blocks = [];
  let list = null;

  const flush = () => {
    if (list) blocks.push(list);
    list = null;
  };

  lines.forEach((raw) => {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
    const ordered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    if (bullet || ordered) {
      const type = bullet ? "ul" : "ol";
      if (!list || list.type !== type) {
        flush();
        list = { type, items: [] };
      }
      list.items.push((bullet || ordered)[1]);
      return;
    }
    flush();
    if (!line.trim()) blocks.push({ type: "gap" });
    else if (heading) blocks.push({ type: "h", text: heading[1] });
    else blocks.push({ type: "p", text: line });
  });
  flush();

  // Líneas consecutivas forman un mismo párrafo.
  const merged = [];
  blocks.forEach((b) => {
    const prev = merged[merged.length - 1];
    if (b.type === "p" && prev?.type === "p") prev.text += "\n" + b.text;
    else if (b.type !== "gap") merged.push(b);
  });

  return (
    <div className="prose-chat">
      {merged.map((b, i) => {
        if (b.type === "h") return <h4 key={i}>{inline(b.text, i)}</h4>;
        if (b.type === "ul" || b.type === "ol") {
          const Tag = b.type;
          return (
            <Tag key={i}>
              {b.items.map((it, j) => (
                <li key={j}>{inline(it, `${i}-${j}`)}</li>
              ))}
            </Tag>
          );
        }
        return (
          <p key={i} className="whitespace-pre-wrap">
            {inline(b.text, i)}
          </p>
        );
      })}
    </div>
  );
}
