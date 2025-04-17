import streamlit as st
import tempfile
import pandas as pd
import random
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def vizAggrid(activites: pd.DataFrame, title: str):
    st.subheader(f"{title}")

    # Affichage interactif
    gb = GridOptionsBuilder.from_dataframe(activites)
    gb.configure_pagination()
    grid_options = gb.build()
    AgGrid(activites, gridOptions=grid_options, height=300)

    col1, col2 = st.columns(2)

    # --- Bouton PDF ---
    with col1:
        if st.button("📄 Générer le PDF", key=title):
            if 'activites' in locals() or 'activites' in globals():
                pdf_path = generate_pdf("Tableau des Activités", activites)
            
                # Télécharger le fichier PDF généré
                if pdf_path:
                    with open(pdf_path.name, "rb") as f:
                        st.download_button(
                            key=f"btn_{random.randint(1, 1000000)}",
                            label="⬇️ Télécharger le PDF",
                            data=f,
                            file_name=f"activites_{random.randint(1, 100000)}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.error("Le DataFrame 'activites' n'est pas défini")   

    # --- Bouton Excel ---
    with col2:
        excel_file = convert_df_to_excel(activites)
        st.download_button(
            key=f"btn_{random.randint(1, 1000000)}",
            label="📥 Exporter en Excel",
            data=excel_file,
            file_name=f"activites_{random.randint(1,100000)}.xlsx",
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
def generate_pdf(title, activites):
    try:
        # Vérifier si le DataFrame est vide
        if activites.empty:
            raise ValueError("Le DataFrame des activités est vide")
            
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc = SimpleDocTemplate(pdf_file.name, pagesize=landscape(letter))
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        p_style = ParagraphStyle(
            name='Normal',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            spaceBefore=2,
            spaceAfter=2
        )
        
        # Titre
        title_style = styles['Title']
        title_style.alignment = 1
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph("<br/>", styles['Normal']))
        
        # Préparation des données avec vérification de nullité
        data = []
        
        # En-têtes
        header_row = [Paragraph(str(col), p_style) for col in activites.columns]
        data.append(header_row)
        
        # Données
        for _, row in activites.iterrows():
            data_row = []
            for item in row:
                text = str(item) if not pd.isna(item) else ""
                data_row.append(Paragraph(text, p_style) if len(text) > 50 else text)
            data.append(data_row)
        
        # Vérification que nous avons des données
        if len(data) == 0 or len(data[0]) == 0:
            raise ValueError("Aucune donnée à afficher dans le PDF")
        
        # Création du tableau avec protection contre les index out of range
        try:
            table = Table(data, repeatRows=1)
            
            # Style du tableau
            style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4B6A88')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 9),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F7F7F7')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('FONTSIZE', (0,1), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 3),
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
            ])
            table.setStyle(style)
            
            # Calcul des largeurs de colonnes sécurisé
            if len(data) > 0 and len(data[0]) > 0:
                col_widths = []
                for i in range(len(data[0])):
                    try:
                        max_len = max(
                            len(str(row[i])) if i < len(row) else 0 
                            for row in data[:20]  # Seulement les 20 premières lignes
                        )
                        col_widths.append(min(max(max_len * 2.5, 80), 300))  # Entre 80 et 300
                    except:
                        col_widths.append(100)  # Valeur par défaut si erreur
                
                table._argW = col_widths
            
            elements.append(table)
            
        except Exception as table_error:
            raise ValueError(f"Erreur lors de la création du tableau: {str(table_error)}")
        
        # Génération du PDF
        doc.build(elements)
        return pdf_file.name
    
    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF: {str(e)}")
        return None