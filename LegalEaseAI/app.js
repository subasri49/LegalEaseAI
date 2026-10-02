"use strict";
const $ = id => document.getElementById(id);
const LS = { key: "legalease_api_key", models: "legalease_models", hist: "legalease_history" };
let current = { id: null, text: "", type: "Legal Document", terms: "" };

const SYSTEM = "You are a senior legal drafting assistant. You draft clear, formal, well-structured legal documents using standard clauses. Output PLAIN TEXT only: no markdown symbols (no #, *, or backticks). Use numbered section headings such as '1. Services:' on their own line. Where facts are unknown, use square-bracket placeholders like [Address]. Never invent party names, amounts or dates that the user did not provide.";

// ---------- text helpers (ported from ai_core/generator.py)
const REPL = { "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ", "\u2022": "-" };
function sanitize(t) {
  if (!t) return "";
  for (const [a, b] of Object.entries(REPL)) t = t.split(a).join(b);
  return t.replace(/\r\n/g, "\n").replace(/`/g, "").replace(/^#{1,6}\s*/gm, "")
    .replace(/^\s*\*\s+/gm, "- ").replace(/\*+/g, "").replace(/\n{3,}/g, "\n\n").trim();
}
const splitTerms = t => (t || "").replace(/\n/g, ";").split(";").map(s => s.trim()).filter(Boolean);
function isHeading(l) {
  const s = l.trim();
  if (!s || s.length > 80) return false;
  if (/^(ARTICLE|SECTION)\s+\w+/i.test(s)) return true;
  if (/^\d+(\.\d+)*[.)]\s+\S/.test(s) && !s.endsWith(".")) return true;
  if (s === s.toUpperCase() && /[A-Z]/.test(s) && s.length > 3) return true;
  return s.endsWith(":") && s.split(/\s+/).length <= 7;
}
const isBullet = l => /^\s*(-|[a-z]\)|\([a-z]\))\s+/.test(l);
function parseBlocks(text) {
  const out = []; let first = true;
  for (const line of sanitize(text).split("\n")) {
    if (!line.trim()) continue;
    if (first) { out.push(["title", line.trim()]); first = false; }
    else if (isHeading(line)) out.push(["heading", line.trim()]);
    else if (isBullet(line)) out.push(["bullet", line.replace(/^\s*-\s+/, "").trim()]);
    else out.push(["para", line.trim()]);
  }
  return out;
}
const esc = s => s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const slug = t => t.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "document";

// ---------- Gemini (browser -> Google directly)
async function generate(type, parties, terms, dates) {
  const key = $("apiKey").value.trim();
  if (!key) throw new Error("Please paste your Gemini API key in the settings box first.");
  const list = splitTerms(terms).map(t => "- " + t).join("\n") || "- (none provided)";
  const prompt = `Generate a comprehensive legal document titled '${type}'.\nInvolved parties: ${parties}\nEffective date: ${dates}\nTerms and conditions to include (each must appear as a clause):\n${list}\n\nRequirements:\n- First line: the document title in capital letters.\n- Use a formal legal structure: preamble/recitals, definitions where useful, numbered sections with legal clauses, governing law, severability, entire agreement, and a signature block for every party.\n- Plain text only, no markdown.`;
  let lastErr;
  for (const model of $("models").value.split(",").map(m => m.trim()).filter(Boolean)) {
    try {
      const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-goog-api-key": key },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: SYSTEM }] },
          contents: [{ role: "user", parts: [{ text: prompt }] }],
          generationConfig: { temperature: 0.3 }
        })
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error?.message || r.statusText);
      const text = (data.candidates?.[0]?.content?.parts || []).map(p => p.text || "").join("").trim();
      if (text) return text;
      lastErr = new Error(`Model ${model} returned an empty response`);
    } catch (e) {
      lastErr = e;
      if (/API key/i.test(e.message)) break; // a different model will not fix a bad key
    }
  }
  throw new Error("Gemini generation failed: " + (lastErr?.message || "unknown error"));
}

// ---------- history (localStorage replaces SQLite)
const loadHist = () => { try { return JSON.parse(localStorage.getItem(LS.hist)) || []; } catch { return []; } };
const saveHist = h => localStorage.setItem(LS.hist, JSON.stringify(h.slice(0, 50)));
function renderHistory() {
  const h = loadHist(), box = $("history");
  box.innerHTML = h.length ? "" : '<p class="muted">No documents yet.</p>';
  h.forEach(it => {
    const b = document.createElement("button");
    b.textContent = `#${it.id} · ${it.type.slice(0, 28)}`;
    b.onclick = () => show(it.id, it.content, it.type, it.terms);
    box.appendChild(b);
  });
}

// ---------- UI
function show(id, text, type, terms) {
  current = { id, text: sanitize(text), type, terms };
  $("result").hidden = false; $("editBox").hidden = true;
  $("editor").value = current.text;
  $("preview").innerHTML = parseBlocks(current.text).map(([k, c]) => {
    c = esc(c);
    return k === "title" ? `<h3>${c}</h3>` : k === "heading" ? `<h4>${c}</h4>` : k === "bullet" ? `<div class="b">&bull; ${c}</div>` : `<p>${c}</p>`;
  }).join("");
}
function msg(text, cls) { $("msg").innerHTML = text ? `<div class="${cls}">${esc(text)}</div>` : ""; }

$("generate").onclick = async () => {
  const v = ["docType", "parties", "terms", "dates"].map(i => $(i).value.trim());
  if (v.some(x => !x)) return msg("Please fill in all four fields.", "err");
  const btn = $("generate"); btn.disabled = true; msg("Drafting your document with Gemini...", "ok");
  try {
    const text = await generate(...v);
    const h = loadHist(), id = (h[0]?.id || 0) + 1;
    h.unshift({ id, type: v[0], parties: v[1], terms: v[2], dates: v[3], content: text, created: new Date().toISOString() });
    saveHist(h); renderHistory(); show(id, text, v[0], v[2]);
    msg("✅ Document Generated Successfully!", "ok");
  } catch (e) { msg(e.message, "err"); }
  btn.disabled = false;
};
$("editBtn").onclick = () => { $("editBox").hidden = !$("editBox").hidden; };
$("editor").oninput = () => { current.text = $("editor").value; };
$("saveBtn").onclick = () => {
  const h = loadHist(), it = h.find(x => x.id === current.id);
  if (it) { it.content = current.text; saveHist(h); msg("Saved.", "ok"); } else msg("Could not save edits.", "err");
};
$("apiKey").onchange = () => localStorage.setItem(LS.key, $("apiKey").value.trim());
$("models").onchange = () => localStorage.setItem(LS.models, $("models").value.trim());

// ---------- downloads
function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
const base = () => slug(current.type);
async function logoBytes() { // relative path -> works under /repo-name/ on GitHub Pages
  try { const r = await fetch("Image/Logo.png"); return r.ok ? new Uint8Array(await r.arrayBuffer()) : null; } catch { return null; }
}
$("dlTxt").onclick = () => download(new Blob([sanitize(current.text)], { type: "text/plain" }), base() + ".txt");

$("dlDocx").onclick = async () => {
  const { Document, Packer, Paragraph, TextRun, AlignmentType, ImageRun, Table, TableRow, TableCell, WidthType, Footer } = window.docx;
  const kids = [], logo = await logoBytes();
  if (logo) kids.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ data: logo, transformation: { width: 150, height: 45 } })] }));
  for (const [k, c] of parseBlocks(current.text)) {
    if (k === "title") kids.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: c, bold: true, size: 32 })] }));
    else if (k === "heading") kids.push(new Paragraph({ spacing: { before: 200 }, keepNext: true, children: [new TextRun({ text: c, bold: true })] }));
    else if (k === "bullet") kids.push(new Paragraph({ bullet: { level: 0 }, children: [new TextRun(c)] }));
    else kids.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, children: [new TextRun(c)] }));
  }
  const items = splitTerms(current.terms);
  if (items.length) {
    kids.push(new Paragraph({ spacing: { before: 280 }, children: [new TextRun({ text: "Summary of Key Terms", bold: true })] }));
    const cell = (t, w, b) => new TableCell({ width: { size: w, type: WidthType.PERCENTAGE }, children: [new Paragraph({ children: [new TextRun({ text: t, bold: !!b })] })] });
    kids.push(new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows: [
      new TableRow({ children: [cell("No.", 10, 1), cell("Term / Condition", 90, 1)] }),
      ...items.map((t, i) => new TableRow({ children: [cell(String(i + 1), 10), cell(sanitize(t), 90)] }))
    ] }));
  }
  const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "LegalEase | AI-generated draft - have a qualified lawyer review before signing", italics: true, size: 16 })] })] });
  const doc = new Document({ title: current.type, creator: "LegalEase",
    styles: { default: { document: { run: { font: "Times New Roman", size: 24 } } } },
    sections: [{ footers: { default: footer }, children: kids }] });
  download(await Packer.toBlob(doc), base() + ".docx");
};

$("dlPdf").onclick = async () => {
  const { jsPDF } = window.jspdf, pdf = new jsPDF({ unit: "mm", format: "a4" });
  const W = 170, left = 20, bottom = 275; let y = 20;
  const logo = await logoBytes();
  if (logo) { let s = ""; logo.forEach(b => s += String.fromCharCode(b)); pdf.addImage("data:image/png;base64," + btoa(s), "PNG", 84, 8, 42, 12.6); y = 28; }
  const write = (t, style, size, lh, align, gap) => {
    pdf.setFont("helvetica", style); pdf.setFontSize(size);
    for (const line of pdf.splitTextToSize(t, W)) {
      if (y > bottom) { pdf.addPage(); y = 20; }
      pdf.text(line, align === "C" ? 105 : left, y, { align: align === "C" ? "center" : "left" }); y += lh;
    }
    y += gap;
  };
  for (const [k, c] of parseBlocks(current.text)) {
    if (k === "title") write(c, "bold", 15, 7, "C", 4);
    else if (k === "heading") { y += 2; write(c, "bold", 11, 6, "L", 1); }
    else if (k === "bullet") write("-  " + c, "normal", 10.5, 5.2, "L", 1);
    else write(c, "normal", 10.5, 5.2, "L", 2);
  }
  const items = splitTerms(current.terms);
  if (items.length) { y += 4; write("Summary of Key Terms", "bold", 11, 6, "L", 1); items.forEach(t => write("-  " + sanitize(t), "normal", 10.5, 5.2, "L", 1)); }
  const n = pdf.getNumberOfPages();
  for (let i = 1; i <= n; i++) {
    pdf.setPage(i); pdf.setFont("helvetica", "italic"); pdf.setFontSize(8);
    pdf.text(`LegalEase | AI-generated draft - have a qualified lawyer review before signing | Page ${i}/${n}`, 105, 288, { align: "center" });
  }
  pdf.save(base() + ".pdf");
};

// ---------- init
$("apiKey").value = localStorage.getItem(LS.key) || "";
$("models").value = localStorage.getItem(LS.models) || $("models").value;
renderHistory();