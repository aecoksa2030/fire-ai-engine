"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { Button } from "@/components/ui/button";

// react-pdf needs pdf.js's worker script. Loaded from a CDN at the
// version pinned in package.json — this runs in the END USER's browser
// at runtime (which has normal internet access), not in any restricted
// build/dev sandbox, so a CDN reference here is the standard, documented
// way to wire this up (self-hosting the worker file is only needed if a
// deployment target has no outbound internet at all for site visitors,
// which isn't the case here).
pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

/** Pan/zoom PDF page viewer — the direct replacement for the Streamlit
 * app's plotly-based `px.imshow` viewer (see frontend/app.py). Same
 * interaction model (scroll wheel = zoom, drag = pan) but as plain DOM +
 * CSS transforms, so it fully respects the app's theme instead of
 * needing its background color hardcoded and manually kept in sync. */
// Dense CAD-exported drawings (see the rotation/rendering comments in
// app/routers/process.py) are full of fine linework and small text — a
// generic web-viewer default width looks fuzzy on them even at 100%
// zoom, so the base render width here is well above what a normal
// document PDF would need.
const BASE_RENDER_WIDTH = 1400;

export function PdfViewer({ file }: { file: File | string }) {
  const [numPages, setNumPages] = useState(0);
  const [pageNum, setPageNum] = useState(1);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragState = useRef<{ startX: number; startY: number; offX: number; offY: number } | null>(null);

  // The CSS transform below applies `scale` instantly for smooth
  // wheel-zoom feedback, but actually re-rasterizing the PDF page at a
  // matching resolution (via <Page>'s `width`) on every wheel tick would
  // mean dozens of expensive re-renders per second while scrolling. So
  // <Page> is fed this DEBOUNCED value instead — it only catches up to
  // the live `scale` ~150ms after the wheel/zoom-button activity settles,
  // trading a brief moment of CSS-stretched softness while actively
  // zooming for a crisp re-render once you stop, instead of staying
  // permanently blurry at every zoom level the way a fixed render width
  // did before (the actual cause of the "pixelated" complaint — the
  // canvas was always rasterized once at a small fixed width and then
  // only ever stretched visually via CSS, never redrawn at the zoomed
  // resolution).
  const [renderScale, setRenderScale] = useState(1);
  useEffect(() => {
    const id = setTimeout(() => setRenderScale(scale), 150);
    return () => clearTimeout(id);
  }, [scale]);

  const onDocLoad = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNum(1);
    setScale(1);
    setRenderScale(1);
    setOffset({ x: 0, y: 0 });
  }, []);

  function onWheel(e: React.WheelEvent) {
    e.preventDefault();
    const delta = -e.deltaY * 0.0015;
    setScale((s) => Math.min(4, Math.max(0.3, s + delta)));
  }

  function onMouseDown(e: React.MouseEvent) {
    dragState.current = { startX: e.clientX, startY: e.clientY, offX: offset.x, offY: offset.y };
  }
  function onMouseMove(e: React.MouseEvent) {
    if (!dragState.current) return;
    const dx = e.clientX - dragState.current.startX;
    const dy = e.clientY - dragState.current.startY;
    setOffset({ x: dragState.current.offX + dx, y: dragState.current.offY + dy });
  }
  function endDrag() {
    dragState.current = null;
  }

  return (
    <div className="rounded-[var(--radius-md)] border border-border-subtle bg-bg-elevated overflow-hidden">
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-border-subtle text-xs text-text-secondary">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={() => setPageNum((p) => Math.max(1, p - 1))} disabled={pageNum <= 1}>
            ‹
          </Button>
          <span>
            {pageNum} / {numPages || 1}
          </span>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => setPageNum((p) => Math.min(numPages, p + 1))}
            disabled={pageNum >= numPages}
          >
            ›
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={() => setScale((s) => Math.max(0.3, s - 0.2))}>
            −
          </Button>
          <span>{Math.round(scale * 100)}%</span>
          <Button size="sm" variant="secondary" onClick={() => setScale((s) => Math.min(4, s + 0.2))}>
            +
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setScale(1);
              setRenderScale(1);
              setOffset({ x: 0, y: 0 });
            }}
          >
            Reset
          </Button>
        </div>
      </div>

      <div
        className="relative h-[520px] overflow-hidden bg-bg-elevated-2 cursor-grab active:cursor-grabbing select-none"
        onWheel={onWheel}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={endDrag}
        onMouseLeave={endDrag}
      >
        <div
          className="absolute top-1/2 left-1/2 origin-center transition-transform duration-75"
          style={{
            // The page is actually rasterized at BASE_RENDER_WIDTH *
            // renderScale (see <Page> below); this transform's own scale
            // factor is only the small remaining gap between the live
            // `scale` and the debounced `renderScale` that fed the last
            // real render, so it's a light touch-up, not the whole zoom.
            transform: `translate(-50%, -50%) translate(${offset.x}px, ${offset.y}px) scale(${scale / renderScale})`,
          }}
        >
          <Document file={file} onLoadSuccess={onDocLoad} loading={<ViewerLoading />}>
            <Page
              pageNumber={pageNum}
              width={Math.round(BASE_RENDER_WIDTH * renderScale)}
              renderAnnotationLayer={false}
              renderTextLayer={false}
            />
          </Document>
        </div>
      </div>
    </div>
  );
}

function ViewerLoading() {
  return (
    <div className="h-[400px] w-[300px] flex items-center justify-center text-text-muted text-sm">
      Loading…
    </div>
  );
}
