"use client";

import { useRef, useState, useCallback } from "react";

type Status = "idle" | "working" | "copied" | "downloaded" | "error";

interface Props {
  filename?: string;
  children: React.ReactNode;
}

export function ShareableCard({ filename = "karta", children }: Props) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<Status>("idle");

  const capture = useCallback(async () => {
    if (!cardRef.current) return null;
    const { default: html2canvas } = await import("html2canvas");
    return html2canvas(cardRef.current, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: null,
      logging: false,
    });
  }, []);

  const handleCopy = async () => {
    setStatus("working");
    try {
      const canvas = await capture();
      if (!canvas) throw new Error("capture failed");
      const blob = await new Promise<Blob>((res, rej) =>
        canvas.toBlob((b) => (b ? res(b) : rej(new Error("blob failed"))), "image/png")
      );
      await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
      setStatus("copied");
      setTimeout(() => setStatus("idle"), 2000);
    } catch {
      setStatus("error");
      setTimeout(() => setStatus("idle"), 2000);
    }
  };

  const handleDownload = async () => {
    setStatus("working");
    try {
      const canvas = await capture();
      if (!canvas) throw new Error("capture failed");
      const a = document.createElement("a");
      a.href = canvas.toDataURL("image/png");
      a.download = `${filename}.png`;
      a.click();
      setStatus("downloaded");
      setTimeout(() => setStatus("idle"), 2000);
    } catch {
      setStatus("error");
      setTimeout(() => setStatus("idle"), 2000);
    }
  };

  const label: Record<Status, string> = {
    idle: "Sdílet",
    working: "…",
    copied: "Zkopírováno ✓",
    downloaded: "Staženo ✓",
    error: "Chyba",
  };

  const canCopy = typeof navigator !== "undefined" && "clipboard" in navigator && "ClipboardItem" in window;

  return (
    <div className="flex flex-col gap-2">
      <div ref={cardRef}>{children}</div>
      <div className="flex gap-2 ml-1">
        {canCopy && (
          <button
            onClick={handleCopy}
            disabled={status === "working"}
            className="font-sans text-xs px-2.5 py-1 rounded-badge bg-surface-2 border border-border text-muted-foreground hover:border-navy-6 hover:text-navy-9 transition-colors disabled:opacity-50"
          >
            {status === "copied" || status === "error" ? label[status] : "📋 Kopírovat"}
          </button>
        )}
        <button
          onClick={handleDownload}
          disabled={status === "working"}
          className="font-sans text-xs px-2.5 py-1 rounded-badge bg-surface-2 border border-border text-muted-foreground hover:border-navy-6 hover:text-navy-9 transition-colors disabled:opacity-50"
        >
          {status === "downloaded" || status === "error" ? label[status] : "⬇ Stáhnout"}
        </button>
        {status === "working" && (
          <span className="font-sans text-xs text-muted-foreground py-1">…</span>
        )}
      </div>
    </div>
  );
}
