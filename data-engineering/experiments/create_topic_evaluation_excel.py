import csv
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR / "outputs" / "preprocessing_experiments"
    / "new_articles_protected" / "topic_predictions.csv"
)

OUTPUT_FILE = (
    BASE_DIR / "outputs" / "preprocessing_experiments"
    / "new_articles_protected" / "manual_topic_evaluation.xlsx"
)


def read_predictions():
    with INPUT_FILE.open(
        encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def style_sheet(ws, widths):
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.row_dimensions[1].height = 32

    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            "solid", fgColor="244062"
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    for column, width in widths.items():
        ws.column_dimensions[column].width = width

    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(
                vertical="top", wrap_text=True
            )


def add_evaluation_validation(ws, column_letter):
    validation = DataValidation(
        type="list",
        formula1='"Relevan,Sebagian relevan,Tidak relevan"',
        allow_blank=True,
    )
    validation.error = "Pilih salah satu kategori yang tersedia."
    validation.errorTitle = "Penilaian tidak valid"
    validation.prompt = "Pilih kategori berdasarkan kesesuaian isi berita."
    validation.promptTitle = "Evaluasi relevansi"
    ws.add_data_validation(validation)
    validation.add(f"{column_letter}2:{column_letter}{ws.max_row}")


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    predictions = read_predictions()

    assigned = [
        row for row in predictions
        if int(row["topic_id"]) != -1
    ]

    outliers = [
        row for row in predictions
        if int(row["topic_id"]) == -1
    ]

    wb = Workbook()

    # Lembar evaluasi topik
    ws = wb.active
    ws.title = "Evaluasi Topik"

    headers = [
        "Topic ID",
        "Nama Topik Model",
        "ID Artikel",
        "Judul Berita",
        "Sumber",
        "Tanggal Publikasi",
        "URL",
        "Penilaian Manual",
        "Catatan Evaluasi",
    ]
    ws.append(headers)

    assigned.sort(
        key=lambda row: (
            int(row["topic_id"]),
            row["title"].lower(),
        )
    )

    for row in assigned:
        ws.append([
            int(row["topic_id"]),
            row["topic_name"],
            row["id"],
            row["title"],
            row["source"],
            row["published_at"],
            row["url"],
            "",
            "",
        ])

    style_sheet(
        ws,
        {
            "A": 12, "B": 38, "C": 13,
            "D": 65, "E": 20, "F": 32,
            "G": 55, "H": 23, "I": 55,
        },
    )

    add_evaluation_validation(ws, "H")

    # Lembar outlier
    out = wb.create_sheet("Outlier")

    out.append([
        "ID Artikel",
        "Judul Berita",
        "Sumber",
        "Tanggal Publikasi",
        "URL",
        "Penilaian Manual",
        "Catatan Evaluasi",
    ])

    for row in outliers:
        out.append([
            row["id"],
            row["title"],
            row["source"],
            row["published_at"],
            row["url"],
            "",
            "",
        ])

    style_sheet(
        out,
        {
            "A": 13, "B": 65, "C": 20,
            "D": 32, "E": 55, "F": 23, "G": 55,
        },
    )

    add_evaluation_validation(out, "F")

    # Petunjuk penilaian
    guide = wb.create_sheet("Petunjuk")

    instructions = [
        ["PANDUAN EVALUASI MANUAL TOPIK"],
        ["Kategori", "Kriteria"],
        ["Relevan", "Artikel membahas isu atau peristiwa yang sama."],
        ["Sebagian relevan", "Artikel masih satu tema umum, tetapi isu atau peristiwanya berbeda."],
        ["Tidak relevan", "Artikel tidak memiliki hubungan topik yang berarti."],
        ["Catatan", "Tuliskan alasan singkat jika artikel dinilai sebagian relevan atau tidak relevan."],
        ["Penting", "Nilai berdasarkan isi judul dan ringkasan yang tersedia, bukan hanya kemiripan kata."],
        ["Outlier", "Untuk artikel outlier, tentukan apakah isunya jelas atau belum dapat ditentukan."],
        ["Database", "Pengisian Excel ini tidak mengubah database maupun model BERTopic."],
    ]

    for row in instructions:
        guide.append(row)

    guide.merge_cells("A1:B1")
    guide["A1"].font = Font(
        bold=True, size=14, color="FFFFFF"
    )
    guide["A1"].fill = PatternFill(
        "solid", fgColor="244062"
    )
    guide["A1"].alignment = Alignment(
        horizontal="center"
    )

    for cell in guide[2]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            "solid", fgColor="4472C4"
        )

    guide.column_dimensions["A"].width = 24
    guide.column_dimensions["B"].width = 100

    for row in guide.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(
                vertical="top", wrap_text=True
            )

    guide.freeze_panes = "A2"

    OUTPUT_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )

    wb.save(OUTPUT_FILE)

    print("=" * 60)
    print("FILE EVALUASI MANUAL BERHASIL DIBUAT")
    print("=" * 60)
    print("Artikel bertopik :", len(assigned))
    print("Artikel outlier  :", len(outliers))
    print("Total artikel    :", len(predictions))
    print("Jumlah sheet     :", len(wb.sheetnames))
    print("Lokasi file      :", OUTPUT_FILE)
    print("\nDatabase dan model tidak diubah.")


if __name__ == "__main__":
    main()
