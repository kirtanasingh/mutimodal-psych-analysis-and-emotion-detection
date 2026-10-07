import io
from datetime import datetime, timezone
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.models.clinical import ReportStatus

from app.models.clinical import EmotionPrediction, FusionResult, Report, Session as ClinicalSession

EMOTIONS = ("anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise")
COLORS = ("#c2524a", "#7a9e3f", "#6b5b95", "#d4a24c", "#8a94a6", "#5b7fa6", "#c77dbb")
LIMITATIONS = (
    "This is an AI-assisted analysis tool, not a diagnostic instrument. "
    "The underlying models were trained on the MELD dataset, which contains scripted dialogue rather than clinical data. "
    "All observations require review by a qualified professional."
)


def generate_report_pdf(db: Session, session_id: int) -> bytes:
    session = db.get(ClinicalSession, session_id)
    if session is None or session.transcript is None:
        raise ValueError("Session data is not available for report generation")
    fusion_rows = list(db.scalars(select(FusionResult).where(FusionResult.session_id == session_id)))
    averages = {
        emotion: sum(float(row.probabilities_json.get(emotion, 0)) for row in fusion_rows) / max(len(fusion_rows), 1)
        for emotion in EMOTIONS
    }
    chart_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    chart_path = Path(chart_file.name)
    chart_file.close()
    try:
        fig, axis = plt.subplots(figsize=(7, 3.2))
        axis.barh(list(EMOTIONS), list(averages.values()), color=list(COLORS))
        axis.set_xlim(0, 1)
        axis.set_xlabel("Average probability")
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.grid(axis="x", alpha=.15)
        fig.tight_layout()
        fig.savefig(chart_path, dpi=160, transparent=False)
        plt.close(fig)

        buffer = io.BytesIO()
        styles = getSampleStyleSheet()
        body = styles["BodyText"]
        story = [
            Paragraph("AI-Assisted Psychological Session Analysis", styles["Title"]),
            Spacer(1, 8),
            Paragraph(f"Patient ID: {session.patient.display_id}", body),
            Paragraph(f"Name: {session.patient.basic_info_json.get('full_name', 'Not provided') if session.patient.basic_info_json else 'Not provided'}", body),
            Paragraph(f"Age: {session.patient.basic_info_json.get('age', 'Not provided') if session.patient.basic_info_json else 'Not provided'}", body),
            Paragraph(f"Profession: {session.patient.basic_info_json.get('profession', 'Not provided') if session.patient.basic_info_json else 'Not provided'}", body),
            Paragraph(f"Session Date: {session.session_date}", body),
            Paragraph(f"Duration: {(session.duration_seconds or 0) // 60:02d}:{(session.duration_seconds or 0) % 60:02d}", body),
            Spacer(1, 18),
            Paragraph("Emotion Distribution", styles["Heading2"]),
            Image(str(chart_path), width=6.7 * inch, height=3.05 * inch),
            Paragraph("Modality Comparison", styles["Heading2"]),
        ]
        notable = max(fusion_rows, key=lambda row: row.confidence, default=None)
        prediction_rows = []
        if notable:
            prediction_rows.append(["Window", "Text", "Audio", "Face", "Fusion"])
            for modality in ("text", "audio", "face"):
                prediction = db.scalar(
                    select(EmotionPrediction)
                    .where(
                        EmotionPrediction.session_id == session_id,
                        EmotionPrediction.window_start == notable.window_start,
                        EmotionPrediction.modality == modality,
                    )
                )
                prediction_rows.append([
                    modality.title(),
                    f"{prediction.dominant_emotion} ({prediction.confidence:.0%})" if prediction else "—",
                    "", "", "",
                ])
            prediction_rows.append(["Fusion", "", "", "", f"{notable.dominant_emotion} ({notable.confidence:.0%})"])
        if prediction_rows:
            table = Table(prediction_rows, colWidths=[1.0 * inch] * 5)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#cbd5e1")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.extend([table, Spacer(1, 14)])
        story.append(Paragraph("Transcript Highlights", styles["Heading2"]))
        for segment in session.transcript.segments[:6]:
            story.append(Paragraph(f"<b>{segment.start_time:.1f}s</b> &nbsp; {segment.text}", body))
        story.extend([Spacer(1, 14), Paragraph("Limitations", styles["Heading2"]), Paragraph(LIMITATIONS, body)])

        def footer(canvas, document):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#64748b"))
            canvas.drawCentredString(letter[0] / 2, .45 * inch, "AI-generated observations — professional review required.")
            canvas.restoreState()

        SimpleDocTemplate(buffer, pagesize=letter, rightMargin=.7 * inch, leftMargin=.7 * inch, topMargin=.65 * inch, bottomMargin=.7 * inch).build(story, onFirstPage=footer, onLaterPages=footer)
        content = buffer.getvalue()
        report = db.scalar(select(Report).where(Report.session_id == session_id))
        report_path = Path(settings.upload_dir) / str(session.patient_id) / str(session_id) / "report.pdf"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_bytes(content)
        now = datetime.now(timezone.utc)
        if report is None:
            report = Report(
                session_id=session_id,
                content_json={"average_probabilities": averages},
                pdf_file_path=str(report_path),
                generated_at=now,
                status=ReportStatus.finalized,
            )
            db.add(report)
        else:
            report.content_json = {"average_probabilities": averages}
            report.pdf_file_path = str(report_path)
            report.generated_at = now
            report.status = ReportStatus.finalized
        db.commit()
        return content
    finally:
        chart_path.unlink(missing_ok=True)
