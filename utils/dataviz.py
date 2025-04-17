import streamlit as st
import tempfile
import pandas as pd
import random
import os
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle



def vizAggrid(df: pd.DataFrame, title: str):
    st.subheader(f"{title}")

    # Affichage interactif
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination()
    grid_options = gb.build()
    AgGrid(df, gridOptions=grid_options, height=300)

    col1, col2 = st.columns(2)

    # --- Bouton PDF ---
    with col1:
        if st.button("📄 Générer le PDF", key=title):
            pdf_path = generate_pdf(title, df)
            
            if pdf_path:
                try:
                    # Lecture du contenu binaire
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    # Bouton de téléchargement
                    st.download_button(
                        label="⬇️ Télécharger PDF",
                        data=pdf_bytes,
                        file_name=f"rapport_{title.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                finally:
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)

    # --- Bouton Excel ---
    with col2:
        excel_file = convert_df_to_excel(df)
        st.download_button(
            key=f"btn_{random.randint(1, 1000000)}",
            label="📥 Exporter en Excel",
            data=excel_file,
            file_name=f"df{random.randint(1,100000)}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

# Fonction utilitaire pour convertir un DataFrame en Excel
def convert_df_to_excel(df):
    df = df.copy()
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Activites')
    return output.getvalue()

# Fonction utilitaire pour generer uf document pdf
def generate_pdf(title, df):
    
    try:
        if df.empty:
            raise ValueError("Le DataFrame est vide")

        # Configuration PDF
        pdf_path = os.path.join(tempfile.gettempdir(), f"rapport_{random.randint(1000,9999)}.pdf")
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(letter),
            leftMargin=20,
            rightMargin=20,
            topMargin=50,
            bottomMargin=30
        )

        # Styles optimisés
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=20,
            alignment=1
        )

        # Fonction pour l'en-tête (sans répétition du titre principal)
        def header(canvas, doc):
            canvas.saveState()
            # Pied de page seulement
            canvas.setFont('Helvetica', 8)
            canvas.drawCentredString(doc.width/2, 15, f"Page {doc.page}")
            canvas.restoreState()

        elements = []
        
        # Titre principal (uniquement en première page)
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 15))

        # Préparation des données avec gestion du débordement
        data = []
        col_widths = []
        
        # En-têtes
        header_row = []
        for col in df.columns:
            header_row.append(Paragraph(f"<b>{col}</b>", styles['Normal']))
            # Estimation largeur colonne
            max_len = max(df[col].astype(str).apply(len).max(), len(col))
            col_widths.append(min(max_len * 4, 150))  # Limite à 150 points
            
        data.append(header_row)

        # Données avec gestion des débordements
        for _, row in df.iterrows():
            data_row = []
            for i, item in enumerate(row):
                cell_style = styles['Normal']
                text = str(item) if not pd.isna(item) else ""
                
                # Adaptation du contenu selon la largeur
                if len(text) * 4 > col_widths[i]:  # Si risque de débordement
                    wrapped_text = "<br/>".join([text[j:j+30] for j in range(0, len(text), 30)])
                    data_row.append(Paragraph(wrapped_text, cell_style))
                else:
                    data_row.append(text)
            data.append(data_row)

        # Création du tableau
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style amélioré
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4B6A88')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F7F7F7')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('WORDWRAP', (0,0), (-1,-1), 'CJK'),  # Gestion explicite du débordement
        ]))

        elements.append(table)
        
        # Construction du PDF
        doc.build(
            elements,
            onFirstPage=header,
            onLaterPages=header
        )
        
        return pdf_path

    except Exception as e:
        st.error(f"Erreur génération PDF : {str(e)}")
        return None