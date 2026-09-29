import io

import fitz  # PyMuPDF


class DocumentParserService:

  @staticmethod
  def process_pdf_to_images(file_bytes: bytes) -> list[bytes]:
    """تحويل صفحات الـ PDF إلى بيايتات صور JPEG عالية الوضوح

    This is the default path for ALL providers (Claude, Gemini, Groq) — see
    process.py. A native-PDF-per-page path (split_pdf_to_pages below) was
    tried and reverted: it required baking non-zero /Rotate flags into the
    content stream for reliable results, and that step took ~34 seconds for
    a single page on a real dense CAD export — a non-starter. get_pixmap()
    here always honors page rotation correctly and renders in a fraction of
    a second, which is what this pipeline used successfully before that
    detour and still does.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    image_bytes_list = []

    for page in doc:
      # زوم 2.0 يوفر دقة وضوح ممتازة لقراءة الرموز الصغيرة عبر Gemini
      zoom = 2.0
      mat = fitz.Matrix(zoom, zoom)
      pix = page.get_pixmap(matrix=mat)

      img_bytes = pix.tobytes("jpeg")
      image_bytes_list.append(img_bytes)

    doc.close()
    return image_bytes_list

  @staticmethod
  def split_pdf_to_pages(file_bytes: bytes) -> list[bytes]:
    """تقسيم الـ PDF متعدد الصفحات إلى ملفات PDF منفصلة صفحة بصفحة

    NOT used by default — process.py sends every provider through
    process_pdf_to_images() instead (see its docstring for why). Left here
    in case native PDF is worth revisiting later with a faster
    rotation-normalization approach than pypdf's transfer_rotation_to_content
    (~34s/page on a dense real drawing — see _extract_upright_page).

    Each returned item is a standalone single-page PDF (still valid vector
    PDF bytes) instead of a pre-rendered JPEG — in principle this lets a
    provider read embedded text/linework directly rather than the vision
    model OCR-ing it off a raster image, though note real exports from this
    project had NO embedded text layer at all (checked with `pdffonts` — 0
    fonts; all "text" is vector-outlined shapes), so that particular
    benefit didn't apply here.

    pypdf is imported lazily inside this method (not at module level) so a
    missing/un-rebuilt pypdf dependency can't break process_pdf_to_images,
    the path actually used in production.
    """
    import pypdf  # lazy: only this unused-by-default path needs it

    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    page_pdf_bytes_list = []

    for page_index in range(len(reader.pages)):
      try:
        page_pdf_bytes_list.append(
            DocumentParserService._extract_upright_page(reader, page_index)
        )
      except Exception:
        # Defensive fallback — if the rotation-normalization below ever
        # misbehaves on some edge-case PDF, fall back to a plain page copy
        # via PyMuPDF (keeps the source's original /Rotate flag) instead
        # of dropping the page.
        src = fitz.open(stream=file_bytes, filetype="pdf")
        single_page_doc = fitz.open()
        single_page_doc.insert_pdf(src, from_page=page_index, to_page=page_index)
        page_pdf_bytes_list.append(single_page_doc.tobytes())
        single_page_doc.close()
        src.close()

    return page_pdf_bytes_list

  @staticmethod
  def _extract_upright_page(reader: "pypdf.PdfReader", page_index: int) -> bytes:
    """استخراج صفحة واحدة كملف PDF مستقل مع "تثبيت" الدوران في المحتوى نفسه

    Several real drawing exports (AutoCAD/Distiller PDFs from landscape
    sheets meant to be viewed in portrait, for example) carry a non-zero
    /Rotate flag on the page instead of physically rotated content — fine
    for a normal PDF viewer or for our own get_pixmap() rendering, both of
    which apply /Rotate automatically. But Anthropic's PDF-support docs
    explicitly list "rotate pages to proper upright orientation" as a
    prerequisite for reliable results, which strongly suggests their
    internal PDF-to-image conversion doesn't always honor /Rotate the way
    a full viewer does — plausibly why a sideways (/Rotate 270 etc.) sheet
    can come back with zero detected components while the exact same page
    rendered to an upright JPEG (which always honors /Rotate) works fine.
    This was confirmed against a real rotated sample from this project:
    /Rotate 270, renders correctly with a normal PDF renderer, but is the
    kind of page Anthropic's own guidance calls out as needing pre-rotation.

    pypdf's transfer_rotation_to_content() bakes the /Rotate transform
    directly into the page's content stream and drops /Rotate to 0, so
    every downstream consumer (Claude, Gemini, anything else) sees an
    already-upright page regardless of whether it honors /Rotate at all.
    Verified against this project's actual sample drawing: rendering the
    normalized output produces a pixel-identical upright image to the
    original (rotation-aware) render. The one cost is that baking rotation
    into the content stream decompresses/rewrites it, which can inflate
    file size significantly (~10x seen on a dense CAD export) —
    compress_content_streams() afterward claws most of that back (~2x net
    on the same file), still comfortably inside Claude's 32MB/request and
    Gemini's 50MB inline limits for a single page.

    Also unused by default (see split_pdf_to_pages) — takes ~34s/page on a
    dense real drawing when rotation is non-zero, which is why the
    native-PDF path was reverted. Kept for reference if this is revisited.
    """
    import pypdf  # lazy — see split_pdf_to_pages

    writer = pypdf.PdfWriter()
    writer.add_page(reader.pages[page_index])
    out_page = writer.pages[0]

    if out_page.rotation:
      out_page.transfer_rotation_to_content()
      out_page.compress_content_streams()

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()