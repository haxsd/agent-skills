#!/usr/bin/env python3
"""Original, dependency-light PDF operations CLI for agent workflows."""

from __future__ import annotations

import argparse
import getpass
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape


class PdfToolError(Exception):
    """A user-facing validation or dependency error."""


def require(module_name, package, purpose):
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise PdfToolError(
            f"{purpose} requires {package}. Install it in the selected project "
            f"environment with: python -m pip install {package}"
        ) from exc


def find_input(raw):
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise PdfToolError(f"input file does not exist: {path}")
    return path


def find_output(raw, inputs=(), overwrite=False):
    path = Path(raw).expanduser().resolve()
    if path.exists() and path.is_dir():
        raise PdfToolError(f"output path is a directory: {path}")
    if path in {item.resolve() for item in inputs}:
        raise PdfToolError("output must differ from every input file")
    if path.exists() and not overwrite:
        raise PdfToolError(f"output already exists; pass --overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def find_output_dir(raw):
    path = Path(raw).expanduser().resolve()
    if path.exists() and not path.is_dir():
        raise PdfToolError(f"output directory is a file: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_pages(spec, total):
    if total < 1:
        raise PdfToolError("PDF has no pages")
    text = (spec or "all").strip().lower()
    if text == "all":
        return list(range(1, total + 1))
    selected = []
    for raw_token in text.split(","):
        token = raw_token.strip()
        if not token:
            continue
        if token == "last":
            start = end = total
        elif "-" in token:
            left, right = token.split("-", 1)
            if not left or not right:
                raise PdfToolError(f"invalid page range: {token}")
            try:
                start, end = int(left), int(right)
            except ValueError as exc:
                raise PdfToolError(f"invalid page range: {token}") from exc
        else:
            try:
                start = end = int(token)
            except ValueError as exc:
                raise PdfToolError(f"invalid page number: {token}") from exc
        if start < 1 or end > total or start > end:
            raise PdfToolError(
                f"page range {token} is outside 1..{total} or reversed"
            )
        for page in range(start, end + 1):
            if page not in selected:
                selected.append(page)
    if not selected:
        raise PdfToolError("page selection is empty")
    return selected


def password_from(args, confirm=False):
    env_name = getattr(args, "password_env", "PDF_PASSWORD")
    value = os.environ.get(env_name)
    if value:
        return value
    if sys.stdin.isatty():
        first = getpass.getpass(f"PDF password ({env_name} is unset): ")
        if not first:
            raise PdfToolError("empty PDF password")
        if confirm and getpass.getpass("Confirm PDF password: ") != first:
            raise PdfToolError("PDF passwords do not match")
        return first
    raise PdfToolError(
        f"PDF password required; set environment variable {env_name}"
    )


def open_reader_detailed(path, args, allow_locked=False):
    pypdf = require("pypdf", "pypdf", "reading PDF files")
    reader = pypdf.PdfReader(str(path))
    if not reader.is_encrypted:
        return reader, False, None
    env_name = getattr(args, "password_env", "PDF_PASSWORD")
    if not os.environ.get(env_name):
        if allow_locked:
            return reader, True, None
        raise PdfToolError(
            f"PDF is encrypted; set environment variable {env_name}"
        )
    password = password_from(args)
    if not reader.decrypt(password):
        raise PdfToolError("PDF password was rejected")
    return reader, False, password


def open_reader(path, args, allow_locked=False):
    reader, locked, _ = open_reader_detailed(path, args, allow_locked)
    return reader, locked


def write_json(path, document):
    path = Path(path)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def print_json(document):
    print(json.dumps(document, ensure_ascii=False, indent=2))


def read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PdfToolError(f"invalid JSON input: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PdfToolError("form values must be a JSON object")
    return value


def metadata_dict(reader):
    raw = reader.metadata or {}
    result = {}
    for key, value in raw.items():
        result[str(key).lstrip("/")] = str(value)
    return result


def field_summary(reader, include_values=False):
    fields = reader.get_fields() or {}
    rows = []
    for name, field in sorted(fields.items()):
        row = {
            "name": name,
            "type": str(field.get("/FT", "")).lstrip("/"),
            "required": bool(field.get("/Ff", 0) & 2),
        }
        if include_values and "/V" in field:
            row["value"] = str(field.get("/V"))
        rows.append(row)
    return rows


def widget_count(reader):
    count = 0
    for page in reader.pages:
        annotations = page.get("/Annots") or []
        for reference in annotations:
            obj = (
                reference.get_object()
                if hasattr(reference, "get_object")
                else reference
            )
            if obj.get("/Subtype") == "/Widget":
                count += 1
    return count


def verify_pdf(path, expected_pages=None, password=None):
    pypdf = require("pypdf", "pypdf", "verifying PDF files")
    reader = pypdf.PdfReader(str(path))
    if reader.is_encrypted:
        if password is None or not reader.decrypt(password):
            raise PdfToolError(f"written PDF is unexpectedly locked: {path}")
    pages = len(reader.pages)
    if pages < 1:
        raise PdfToolError(f"written PDF has no pages: {path}")
    if expected_pages is not None and pages != expected_pages:
        raise PdfToolError(
            f"written PDF has {pages} pages; expected {expected_pages}: {path}"
        )
    return pages


def add_pages(writer, reader):
    for page in reader.pages:
        writer.add_page(page)


def report_output(command, path, pages):
    print(
        json.dumps(
            {
                "command": command,
                "output": str(path),
                "pages": pages,
                "verified": True,
            },
            ensure_ascii=False,
        )
    )


def cmd_inspect(args):
    source = find_input(args.input)
    reader, locked = open_reader(source, args, allow_locked=True)
    info = {
        "input": str(source),
        "encrypted": bool(reader.is_encrypted),
        "locked": locked,
        "metadata": metadata_dict(reader),
    }
    if not locked:
        info["pages"] = len(reader.pages)
        info["formFields"] = field_summary(
            reader, include_values=args.show_form_values
        )
        info["widgetCount"] = widget_count(reader)
        if args.preview > 0:
            text = reader.pages[0].extract_text() or ""
            info["firstPagePreview"] = text[: args.preview]
            info["firstPagePreviewTruncated"] = len(text) > args.preview
    if args.output:
        output = find_output(
            args.output, inputs=(source,), overwrite=args.overwrite
        )
        write_json(output, info)
        print(str(output))
    else:
        print_json(info)
    return 0


def cmd_extract_text(args):
    source = find_input(args.input)
    output = find_output(
        args.output, inputs=(source,), overwrite=args.overwrite
    )
    reader, _, password = open_reader_detailed(source, args)
    pages = parse_pages(args.pages, len(reader.pages))
    extracted = []
    if args.layout:
        pdfplumber = require(
            "pdfplumber", "pdfplumber", "layout-aware text extraction"
        )
        options = {"password": password} if password else {}
        with pdfplumber.open(str(source), **options) as document:
            for page_number in pages:
                text = document.pages[page_number - 1].extract_text() or ""
                extracted.append({"page": page_number, "text": text})
    else:
        for page_number in pages:
            text = reader.pages[page_number - 1].extract_text() or ""
            extracted.append({"page": page_number, "text": text})
    if args.format == "json":
        write_json(
            output,
            {
                "source": str(source),
                "layout": args.layout,
                "pages": extracted,
            },
        )
    else:
        chunks = []
        for row in extracted:
            chunks.append(
                f"--- page {row['page']} ---\n{row['text'].rstrip()}\n"
            )
        output.write_text(
            "\n".join(chunks), encoding="utf-8", newline="\n"
        )
    report_output("extract-text", output, len(extracted))
    return 0


def cmd_extract_tables(args):
    source = find_input(args.input)
    output = find_output(
        args.output, inputs=(source,), overwrite=args.overwrite
    )
    reader, _, password = open_reader_detailed(source, args)
    pages = parse_pages(args.pages, len(reader.pages))
    pdfplumber = require("pdfplumber", "pdfplumber", "table extraction")
    rows = []
    options = {"password": password} if password else {}
    with pdfplumber.open(str(source), **options) as document:
        for page_number in pages:
            tables = document.pages[page_number - 1].extract_tables() or []
            rows.append({"page": page_number, "tables": tables})
    write_json(output, {"source": str(source), "pages": rows})
    report_output("extract-tables", output, len(rows))
    return 0


def cmd_merge(args):
    inputs = [find_input(item) for item in args.inputs]
    output = find_output(
        args.output, inputs=inputs, overwrite=args.overwrite
    )
    pypdf = require("pypdf", "pypdf", "merging PDF files")
    writer = pypdf.PdfWriter()
    for source in inputs:
        reader, _ = open_reader(source, args)
        add_pages(writer, reader)
    with output.open("wb") as stream:
        writer.write(stream)
    pages = verify_pdf(output)
    report_output("merge", output, pages)
    return 0


def cmd_split(args):
    source = find_input(args.input)
    output_dir = find_output_dir(args.output_dir)
    reader, _ = open_reader(source, args)
    pages = parse_pages(args.pages, len(reader.pages))
    pypdf = require("pypdf", "pypdf", "splitting PDF files")
    generated = []
    for page_number in pages:
        prefix = args.prefix or source.stem
        output = find_output(
            output_dir / f"{prefix}-p{page_number:03d}.pdf",
            inputs=(source,),
            overwrite=args.overwrite,
        )
        writer = pypdf.PdfWriter()
        writer.add_page(reader.pages[page_number - 1])
        with output.open("wb") as stream:
            writer.write(stream)
        verify_pdf(output, expected_pages=1)
        generated.append(str(output))
    print(
        json.dumps(
            {
                "command": "split",
                "outputs": generated,
                "pages": len(generated),
                "verified": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


def cmd_rotate(args):
    source = find_input(args.input)
    output = find_output(
        args.output, inputs=(source,), overwrite=args.overwrite
    )
    reader, _ = open_reader(source, args)
    selected = set(parse_pages(args.pages, len(reader.pages)))
    pypdf = require("pypdf", "pypdf", "rotating PDF pages")
    writer = pypdf.PdfWriter()
    for index, page in enumerate(reader.pages, 1):
        if index in selected:
            page.rotate(args.angle)
        writer.add_page(page)
    with output.open("wb") as stream:
        writer.write(stream)
    pages = verify_pdf(output, expected_pages=len(reader.pages))
    report_output("rotate", output, pages)
    return 0


def cmd_encrypt(args):
    source = find_input(args.input)
    output = find_output(
        args.output, inputs=(source,), overwrite=args.overwrite
    )
    reader, _ = open_reader(source, args)
    password = password_from(args, confirm=True)
    pypdf = require("pypdf", "pypdf", "encrypting PDF files")
    writer = pypdf.PdfWriter()
    add_pages(writer, reader)
    try:
        writer.encrypt(password, algorithm="AES-256")
    except (TypeError, ValueError) as exc:
        raise PdfToolError(
            "AES-256 encryption is unavailable; upgrade pypdf to 6.x"
        ) from exc
    with output.open("wb") as stream:
        writer.write(stream)
    pages = verify_pdf(output, password=password)
    report_output("encrypt", output, pages)
    return 0


def cmd_decrypt(args):
    source = find_input(args.input)
    output = find_output(
        args.output, inputs=(source,), overwrite=args.overwrite
    )
    reader, _ = open_reader(source, args)
    pypdf = require("pypdf", "pypdf", "decrypting PDF files")
    writer = pypdf.PdfWriter()
    add_pages(writer, reader)
    with output.open("wb") as stream:
        writer.write(stream)
    pages = verify_pdf(output)
    report_output("decrypt", output, pages)
    return 0


def cmd_form_info(args):
    source = find_input(args.input)
    reader, _ = open_reader(source, args)
    fields = field_summary(reader, include_values=args.show_values)
    names = {row["name"] for row in fields}
    widgets = widget_count(reader)
    info = {
        "input": str(source),
        "pages": len(reader.pages),
        "fields": fields,
        "widgetCount": widgets,
    }
    if widgets and not fields:
        info["warning"] = "widgets exist but no canonical AcroForm fields were found"
    print_json(info)
    return 0


def cmd_form_fill(args):
    source = find_input(args.input)
    values = read_json(args.values)
    output = find_output(
        args.output, inputs=(source,), overwrite=args.overwrite
    )
    reader, _ = open_reader(source, args)
    pypdf = require("pypdf", "pypdf", "filling PDF forms")
    writer = pypdf.PdfWriter()
    writer.clone_document_from_reader(reader)
    available = set((writer.get_fields() or {}).keys())
    missing = sorted(set(values) - available)
    if missing:
        raise PdfToolError(f"form fields not found: {missing}")
    normalized = {}
    for name, value in values.items():
        if isinstance(value, bool):
            normalized[name] = "Yes" if value else "Off"
        elif isinstance(value, (str, int, float)):
            normalized[name] = str(value)
        else:
            raise PdfToolError(
                f"unsupported value for field {name}; use string, number, or bool"
            )
    writer.update_page_form_field_values(
        None, normalized, auto_regenerate=False
    )
    with output.open("wb") as stream:
        writer.write(stream)
    pages = verify_pdf(output, expected_pages=len(reader.pages))
    reopened = pypdf.PdfReader(str(output))
    fields = reopened.get_fields() or {}
    mismatches = []
    for name, expected in normalized.items():
        actual = str(fields.get(name, {}).get("/V", ""))
        if actual.startswith("/"):
            actual = actual[1:]
        if actual != expected:
            mismatches.append(
                {"field": name, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise PdfToolError(f"form values did not persist: {mismatches}")
    report_output("form-fill", output, pages)
    return 0


def cmd_create(args):
    inputs = []
    text_path = None
    if args.text_file:
        text_path = find_input(args.text_file)
        inputs.append(text_path)
        body = text_path.read_text(encoding="utf-8-sig")
    elif args.text:
        body = args.text
    else:
        raise PdfToolError("provide --text or --text-file")
    font_path = find_input(args.font_file) if args.font_file else None
    if font_path:
        inputs.append(font_path)
    output = find_output(args.output, inputs=inputs, overwrite=args.overwrite)
    reportlab = require("reportlab", "reportlab", "creating PDF files")
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from reportlab.lib.enums import TA_LEFT

    font_name = "Helvetica"
    if font_path:
        font_name = f"Custom-{font_path.stem}"
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

    page_size = A4 if args.page_size == "a4" else letter
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=22,
        leading=28,
        spaceAfter=14,
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=16,
        spaceAfter=8,
    )

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont(font_name, 8)
        canvas.drawRightString(
            page_size[0] - 18 * mm, 12 * mm, f"Page {document.page}"
        )
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(output),
        pagesize=page_size,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=args.title or "",
        author=args.author or "",
    )
    story = []
    if args.title:
        story.extend([Paragraph(escape(args.title), title_style), Spacer(1, 4)])
    for block in body.replace("\r\n", "\n").split("\n\n"):
        text = "<br/>".join(escape(line) for line in block.split("\n"))
        if text.strip():
            story.append(Paragraph(text, body_style))
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    pages = verify_pdf(output)
    report_output("create", output, pages)
    return 0


def make_text_overlay(path, width, height, text, font_name):
    reportlab = require("reportlab", "reportlab", "creating a watermark")
    from reportlab.pdfgen import canvas

    pdf = canvas.Canvas(str(path), pagesize=(width, height))
    pdf.saveState()
    pdf.setFillAlpha(0.18)
    pdf.setFont(font_name, max(18, min(width, height) / 14))
    pdf.translate(width / 2, height / 2)
    pdf.rotate(35)
    pdf.drawCentredString(0, 0, text)
    pdf.restoreState()
    pdf.save()


def cmd_watermark(args):
    source = find_input(args.input)
    if bool(args.text) == bool(args.stamp):
        raise PdfToolError("provide exactly one of --text or --stamp")
    inputs = [source]
    stamp_path = find_input(args.stamp) if args.stamp else None
    if stamp_path:
        inputs.append(stamp_path)
    output = find_output(args.output, inputs=inputs, overwrite=args.overwrite)
    reader, _ = open_reader(source, args)
    pypdf = require("pypdf", "pypdf", "adding a watermark")
    writer = pypdf.PdfWriter()
    if stamp_path:
        stamp_reader = pypdf.PdfReader(str(stamp_path))
        stamp_page = stamp_reader.pages[0]
        for page in reader.pages:
            page.merge_page(stamp_page)
            writer.add_page(page)
    else:
        font_name = "Helvetica-Bold"
        with tempfile.TemporaryDirectory(prefix="pdf-watermark-") as raw:
            overlay_path = Path(raw) / "overlay.pdf"
            for index, page in enumerate(reader.pages, 1):
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                make_text_overlay(
                    overlay_path, width, height, args.text, font_name
                )
                overlay_reader = pypdf.PdfReader(str(overlay_path))
                page.merge_page(overlay_reader.pages[0])
                writer.add_page(page)
    with output.open("wb") as stream:
        writer.write(stream)
    pages = verify_pdf(output, expected_pages=len(reader.pages))
    report_output("watermark", output, pages)
    return 0


def cmd_render(args):
    source = find_input(args.input)
    output_dir = find_output_dir(args.output_dir)
    reader, _ = open_reader(source, args)
    pages = parse_pages(args.pages, len(reader.pages))
    executable = args.pdftoppm or shutil.which("pdftoppm")
    if not executable:
        raise PdfToolError(
            "pdftoppm was not found. Install Poppler and pass --pdftoppm "
            "with its verified absolute path."
        )
    exe = Path(executable).expanduser().resolve()
    if not exe.is_file():
        raise PdfToolError(f"pdftoppm executable does not exist: {exe}")
    generated = []
    for page_number in pages:
        prefix = output_dir / f"{args.prefix or source.stem}-p{page_number:03d}"
        command = [
            str(exe),
            "-png",
            "-singlefile",
            "-r",
            str(args.dpi),
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            str(source),
            str(prefix),
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        image = prefix.with_suffix(".png")
        if result.returncode != 0 or not image.is_file() or image.stat().st_size == 0:
            detail = (result.stderr or result.stdout or "").strip()[-500:]
            raise PdfToolError(
                f"render failed for page {page_number}: {detail or result.returncode}"
            )
        generated.append(str(image))
    print(
        json.dumps(
            {
                "command": "render",
                "outputs": generated,
                "pages": len(generated),
                "verified": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


def add_password_option(parser):
    parser.add_argument(
        "--password-env",
        default="PDF_PASSWORD",
        help="environment variable holding the PDF password",
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description="Inspect and transform PDFs without shell interpolation."
    )
    parser.add_argument("--version", action="version", version="1.0.0")
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="read metadata and page facts")
    inspect.add_argument("input")
    inspect.add_argument("--output")
    inspect.add_argument("--overwrite", action="store_true")
    inspect.add_argument("--preview", type=int, default=0)
    inspect.add_argument("--show-form-values", action="store_true")
    add_password_option(inspect)
    inspect.set_defaults(func=cmd_inspect)

    text = commands.add_parser("extract-text", help="extract text by page")
    text.add_argument("input")
    text.add_argument("--output", required=True)
    text.add_argument("--pages", default="all")
    text.add_argument("--layout", action="store_true")
    text.add_argument("--format", choices=("txt", "json"), default="txt")
    text.add_argument("--overwrite", action="store_true")
    add_password_option(text)
    text.set_defaults(func=cmd_extract_text)

    tables = commands.add_parser("extract-tables", help="extract tables to JSON")
    tables.add_argument("input")
    tables.add_argument("--output", required=True)
    tables.add_argument("--pages", default="all")
    tables.add_argument("--overwrite", action="store_true")
    add_password_option(tables)
    tables.set_defaults(func=cmd_extract_tables)

    merge = commands.add_parser("merge", help="merge PDFs in input order")
    merge.add_argument("inputs", nargs="+")
    merge.add_argument("--output", required=True)
    merge.add_argument("--overwrite", action="store_true")
    add_password_option(merge)
    merge.set_defaults(func=cmd_merge)

    split = commands.add_parser("split", help="write selected pages as PDFs")
    split.add_argument("input")
    split.add_argument("--output-dir", required=True)
    split.add_argument("--pages", default="all")
    split.add_argument("--prefix")
    split.add_argument("--overwrite", action="store_true")
    add_password_option(split)
    split.set_defaults(func=cmd_split)

    rotate = commands.add_parser("rotate", help="rotate selected pages")
    rotate.add_argument("input")
    rotate.add_argument("--output", required=True)
    rotate.add_argument("--pages", default="all")
    rotate.add_argument("--angle", type=int, choices=(90, 180, 270), required=True)
    rotate.add_argument("--overwrite", action="store_true")
    add_password_option(rotate)
    rotate.set_defaults(func=cmd_rotate)

    encrypt = commands.add_parser("encrypt", help="encrypt with AES-256")
    encrypt.add_argument("input")
    encrypt.add_argument("--output", required=True)
    encrypt.add_argument("--overwrite", action="store_true")
    add_password_option(encrypt)
    encrypt.set_defaults(func=cmd_encrypt)

    decrypt = commands.add_parser("decrypt", help="remove PDF encryption")
    decrypt.add_argument("input")
    decrypt.add_argument("--output", required=True)
    decrypt.add_argument("--overwrite", action="store_true")
    add_password_option(decrypt)
    decrypt.set_defaults(func=cmd_decrypt)

    form_info = commands.add_parser("form-info", help="inspect form fields")
    form_info.add_argument("input")
    form_info.add_argument("--show-values", action="store_true")
    add_password_option(form_info)
    form_info.set_defaults(func=cmd_form_info)

    form_fill = commands.add_parser("form-fill", help="fill interactive fields")
    form_fill.add_argument("input")
    form_fill.add_argument("--values", required=True)
    form_fill.add_argument("--output", required=True)
    form_fill.add_argument("--overwrite", action="store_true")
    add_password_option(form_fill)
    form_fill.set_defaults(func=cmd_form_fill)

    create = commands.add_parser("create", help="create a simple text PDF")
    create.add_argument("--output", required=True)
    create.add_argument("--title")
    create.add_argument("--author")
    create.add_argument("--text")
    create.add_argument("--text-file")
    create.add_argument("--font-file")
    create.add_argument("--page-size", choices=("a4", "letter"), default="a4")
    create.add_argument("--overwrite", action="store_true")
    create.set_defaults(func=cmd_create)

    watermark = commands.add_parser("watermark", help="overlay text or a stamp")
    watermark.add_argument("input")
    watermark.add_argument("--output", required=True)
    watermark.add_argument("--text")
    watermark.add_argument("--stamp")
    watermark.add_argument("--overwrite", action="store_true")
    add_password_option(watermark)
    watermark.set_defaults(func=cmd_watermark)

    render = commands.add_parser("render", help="render selected pages to PNG")
    render.add_argument("input")
    render.add_argument("--output-dir", required=True)
    render.add_argument("--pages", default="all")
    render.add_argument("--dpi", type=int, default=144)
    render.add_argument("--prefix")
    render.add_argument("--pdftoppm")
    add_password_option(render)
    render.set_defaults(func=cmd_render)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except PdfToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
