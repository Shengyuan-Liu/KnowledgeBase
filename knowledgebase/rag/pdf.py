"""Standalone local PDF parsing; does not upload, index, or mutate a library."""

from hashlib import file_digest, sha256
from importlib.metadata import version
from io import BytesIO
import json
from pathlib import Path

from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import ConversionStatus, DocumentStream, InputFormat
from docling.datamodel.pipeline_options import (
    LayoutObjectDetectionOptions, PdfPipelineOptions, TableStructureOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import (
    BoundingBox, ContentLayer, DocItemLabel, DoclingDocument, PictureItem, TableItem, TextItem,
)

from knowledgebase.rag.pdf_models import (
    PdfBlock, PdfCell, PdfExtraction, PdfPage, PdfParserIdentity, PdfRegion,
    PdfTable, PdfWarning,
)
from knowledgebase.rag.pdf_tables import RECOVERY_SETTINGS, recover_collapsed_tables


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def _region(
    document: DoclingDocument, page_no: int, bbox: BoundingBox,
    start: int, end: int, precision: str,
) -> PdfRegion:
    box = bbox.to_top_left_origin(document.pages[page_no].size.height)
    return PdfRegion(
        start_offset=start, end_offset=end, page_index=page_no - 1,
        bbox=(box.l, box.t, box.r, box.b), precision=precision,
    )


def _table(
    item: TableItem, document: DoclingDocument, start: int,
) -> tuple[str, PdfTable]:
    """Serialize each original cell once; preserve merged-cell geometry separately."""
    parts: list[str] = []
    cells: list[PdfCell] = []
    offset = start
    previous_row = None
    for cell in sorted(item.data.table_cells, key=lambda c: (
        c.start_row_offset_idx, c.start_col_offset_idx,
    )):
        if parts:
            separator = "\t" if previous_row == cell.start_row_offset_idx else "\n"
            parts.append(separator)
            offset += len(separator)
        end = offset + len(cell.text)
        # A cell box has no page number. It is unambiguous only for a one-page table.
        regions = ()
        if cell.bbox is not None and len(item.prov) == 1:
            regions = (_region(document, item.prov[0].page_no, cell.bbox, offset, end, "cell"),)
        cells.append(PdfCell(
            text=cell.text, start_offset=offset, end_offset=end,
            row_start=cell.start_row_offset_idx, row_end=cell.end_row_offset_idx,
            column_start=cell.start_col_offset_idx, column_end=cell.end_col_offset_idx,
            column_header=cell.column_header, row_header=cell.row_header,
            row_section=cell.row_section, regions=regions,
        ))
        parts.append(cell.text)
        previous_row = cell.start_row_offset_idx
        offset = end
    return "".join(parts), PdfTable(
        table_id=item.self_ref, rows=item.data.num_rows, columns=item.data.num_cols,
        cells=tuple(cells), caption_refs=tuple(r.cref for r in item.captions),
        note_refs=tuple(r.cref for r in item.footnotes),
    )


def adapt_pdf_document(
    document: DoclingDocument, source: bytes, parser: PdfParserIdentity,
    *, recovered_tables: tuple[str, ...] = (),
) -> PdfExtraction:
    """Freeze ordered Docling output; exact slices do not establish PDF fidelity."""
    parts: list[str] = []
    blocks: list[PdfBlock] = []
    warnings = [
        PdfWarning(code="scope", message=(
            "OCR, visual figure/chart interpretation, and formula understanding are disabled. "
            "Reading order, spacing and table structure are parser estimates; review the original pages."
        )),
        PdfWarning(code="printed_labels_unavailable", message=(
            "Printed page labels are not extracted; page indices refer to physical PDF pages."
        )),
    ]
    headings: list[tuple[int, str]] = []
    offset = 0
    for item, _ in document.iterate_items(included_content_layers=set(ContentLayer)):
        if isinstance(item, PictureItem):
            warnings.append(PdfWarning(
                code="picture_not_interpreted", message="Picture content is omitted; native captions are retained.",
                page_indices=tuple(p.page_no - 1 for p in item.prov), source_ref=item.self_ref,
            ))
            continue
        if not isinstance(item, (TextItem, TableItem)):
            continue
        start = offset + (2 if blocks else 0)
        table = None
        level = None
        kind = "paragraph"
        if isinstance(item, TableItem):
            text, table = _table(item, document, start)
            kind = "table"
            if item.self_ref in recovered_tables:
                warnings.append(PdfWarning(
                    code="native_table_recovery", message=(
                        "A collapsed model table was reconstructed from native PDF rules and text rows. "
                        "Header roles are inferred; review the original page."
                    ), page_indices=tuple(p.page_no - 1 for p in item.prov), source_ref=item.self_ref,
                ))
            warnings.append(PdfWarning(
                code="table_structure_unverified", message=(
                    "Extracted cell/header associations are unverified. Dense and merged tables "
                    "can lose values or group rows incorrectly; consult the original page."
                ), page_indices=tuple(p.page_no - 1 for p in item.prov), source_ref=item.self_ref,
            ))
        else:
            # Docling provenance spans address orig; sanitized text removes list markers.
            text = item.orig
            if item.label in (DocItemLabel.TITLE, DocItemLabel.SECTION_HEADER):
                kind = "heading"
                level = getattr(item, "level", 1)
                while headings and headings[-1][0] >= level:
                    headings.pop()
                headings.append((level, text))
            elif item.label == DocItemLabel.LIST_ITEM:
                kind = "list"
            elif item.label == DocItemLabel.CODE:
                kind = "code"
            elif item.label == DocItemLabel.FORMULA:
                warnings.append(PdfWarning(
                    code="formula_not_understood", message="Native formula text is retained without mathematical interpretation.",
                    page_indices=tuple(p.page_no - 1 for p in item.prov), source_ref=item.self_ref,
                ))
        if not text:
            continue
        end = start + len(text)
        regions = []
        for provenance in item.prov:
            if table is not None:
                region_start, region_end = start, end
            else:
                region_start, region_end = (start + n for n in provenance.charspan)
            regions.append(_region(
                document, provenance.page_no, provenance.bbox,
                region_start, region_end, "table" if table else "block",
            ))
        if not regions:
            warnings.append(PdfWarning(
                code="location_unavailable", message="Parser supplied no original-page location for this block.",
                source_ref=item.self_ref,
            ))
        blocks.append(PdfBlock(
            source_ref=item.self_ref, kind=kind, label=item.label.value, text=text,
            start_offset=start, end_offset=end, heading_path=tuple(t for _, t in headings),
            heading_level=level, regions=tuple(regions), table=table,
        ))
        parts.append(text)
        offset = end
    text = "\n\n".join(parts)
    pages = tuple(PdfPage(page_index=n - 1, width=p.size.width, height=p.size.height)
                  for n, p in sorted(document.pages.items()))
    mapped_pages = {r.page_index for b in blocks for r in b.regions}
    for page in pages:
        if page.page_index not in mapped_pages:
            warnings.append(PdfWarning(
                code="no_extracted_text", message="No supported text was extracted from this page; OCR is disabled.",
                page_indices=(page.page_index,),
            ))
    extraction = PdfExtraction(
        source_hash=sha256(source).hexdigest(), extraction_hash=_digest(text), revision_id="",
        text=text, pages=pages, blocks=tuple(blocks), parser=parser, warnings=tuple(warnings),
    )
    return extraction.model_copy(update={"revision_id": _digest(_json(extraction.model_dump(mode="json")))})


class PdfParser:
    """Reuse a local CPU converter; model assets must be downloaded explicitly first."""

    def __init__(self, artifacts_path: Path):
        options = PdfPipelineOptions(
            artifacts_path=artifacts_path, do_ocr=False, do_table_structure=True,
            do_formula_enrichment=False, do_code_enrichment=False,
            do_picture_description=False, do_picture_classification=False,
            do_chart_extraction=False, enable_remote_services=False,
            layout_options=LayoutObjectDetectionOptions.from_preset("layout_heron_default"),
            table_structure_options=TableStructureOptions(),
            accelerator_options=AcceleratorOptions(device="cpu", num_threads=4),
        )
        # Content hashes identify the actual local model assets, including mutable upstream refs.
        model_files = tuple((str(p.relative_to(artifacts_path)), _file_hash(p))
                            for p in sorted(artifacts_path.rglob("*"))
                            if p.is_file() and ".cache" not in p.parts)
        if not model_files:
            raise ValueError("Download the Docling layout and tableformer assets before constructing PdfParser.")
        settings = options.model_dump(mode="json", serialize_as_any=True)
        settings.pop("artifacts_path")  # Machine-specific paths are not extraction identity.
        settings["collapsed_table_recovery"] = RECOVERY_SETTINGS
        self.identity = PdfParserIdentity(
            name="docling+pdfplumber",
            package_versions=tuple((p, version(p)) for p in (
                "docling", "docling-core", "docling-parse", "docling-ibm-models", "torch",
                "pdfplumber", "pdfminer.six",
            )), settings_json=_json(settings), model_file_hashes=model_files,
        )
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)},
        )

    def parse(self, source: bytes) -> PdfExtraction:
        """Parse PDF bytes into a new immutable revision; partial conversions fail."""
        result = self.converter.convert(DocumentStream(name="source.pdf", stream=BytesIO(source)))
        if result.status != ConversionStatus.SUCCESS:
            raise ValueError(f"PDF conversion did not complete: {result.status.value}; {result.errors}")
        recovered = recover_collapsed_tables(result.document, source)
        return adapt_pdf_document(result.document, source, self.identity, recovered_tables=recovered)
