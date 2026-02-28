import os
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.enums import TA_CENTER

class AudioForensicReportGenerator:
    """Generate audio forensic authentication reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        self.normal_style = self.styles['Normal']
        
    def create_pdf_report(self, output_path, similarity_score, decision, waveform_path, spectrogram_path, audio_names):
        """
        Create a PDF report for audio forensic analysis
        
        Args:
            output_path: Path to save the PDF
            similarity_score: Similarity score (float)
            decision: "Same Speaker" or "Different Speakers"
            waveform_path: Path to the waveform visualization image
            spectrogram_path: Path to the spectrogram visualization image
            audio_names: List of strings (filenames of the compared audios)
        """
        try:
            doc = SimpleDocTemplate(str(output_path), pagesize=letter, 
                                    topMargin=0.75*inch, bottomMargin=0.75*inch)
            story = []
            
            # Title
            story.append(Paragraph("AUDIO FORENSIC ANALYSIS REPORT", self.title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Report info
            report_info = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            if len(audio_names) >= 2:
                report_info += f"<b>Analyzed Files:</b> {audio_names[0]} and {audio_names[1]}"
            story.append(Paragraph(report_info, self.normal_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Authentication Results Table
            story.append(Paragraph("Authentication Results", self.heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            auth_table_data = [
                ["Metric", "Result"],
                ["Decision", decision],
                ["Similarity Score", f"{similarity_score:.4f}"],
                ["Status", "PASSED" if decision == "Same Speaker" else "FAILED/UNVERIFIED"]
            ]
            
            auth_table = Table(auth_table_data, colWidths=[2.5*inch, 3.0*inch])
            auth_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            story.append(auth_table)
            story.append(Spacer(1, 0.4*inch))
            
            # Visualizations
            story.append(Paragraph("Saliency Visualizations", self.heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Waveform
            if Path(waveform_path).exists():
                story.append(Paragraph("Waveform Similarity Saliency", self.styles['Heading3']))
                story.append(Spacer(1, 0.05*inch))
                img = RLImage(str(waveform_path), width=6*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
                
            # Spectrogram
            if Path(spectrogram_path).exists():
                story.append(Paragraph("Spectrogram Similarity Saliency", self.styles['Heading3']))
                story.append(Spacer(1, 0.05*inch))
                img = RLImage(str(spectrogram_path), width=6*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 0.3*inch))
            
            # Footer
            footer_text = "This report was generated automatically. Results should be reviewed by qualified forensic experts."
            footer_style = ParagraphStyle(
                'Footer',
                parent=self.normal_style,
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            story.append(Spacer(1, 0.5*inch))
            story.append(Paragraph(footer_text, footer_style))
            
            doc.build(story)
            return True, "Report generated successfully"
        except Exception as e:
            return False, str(e)
