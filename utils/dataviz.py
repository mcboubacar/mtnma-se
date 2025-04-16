import streamlit as st
from weasyprint import HTML, CSS
import tempfile
import pandas as pd
import base64
import random
from io import BytesIO

from st_aggrid import AgGrid, GridOptionsBuilder

def vizAggrid(activites: pd.DataFrame,title: str):

    st.subheader(f"{title}")

    # Affichage interactif

    gb = GridOptionsBuilder.from_dataframe(activites)
    gb.configure_pagination()
    grid_options = gb.build()
    AgGrid(activites, gridOptions=grid_options, height=300)

    # Boutons dans une colonne
    random.randint(1,10000000)
    col1, col2 = st.columns(2)

    # --- Bouton PDF ---
    with col1:
        if st.button("📄 Générer le PDF",key=title):
            # HTML stylisé avec titre
            html_content = f"""
            <html>
            <head>
                <style>
                    h1 {{
                        text-align: center;
                        color: #333;
                        font-family: 'Arial', sans-serif;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        font-size: 12px;
                    }}
                    th, td {{
                        border: 1px solid #ccc;
                        padding: 6px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                </style>
            </head>
            <body>
                {activites.to_html(index=False)}
            </body>
            </html>
            """

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                HTML(string=html_content).write_pdf(tmpfile.name)
                with open(tmpfile.name, "rb") as f:
                    st.download_button(
                        key=f"btn_{random.randint(1, 1000000)}",
                        label="⬇️ Télécharger le PDF",
                        data=f,
                        file_name=f"pdf_{random.randint(1,100000)}.pdf",
                        mime="application/pdf"
                    )

    # --- Bouton Excel ---
    with col2:
        excel_file = convert_df_to_excel(activites)
        st.download_button(
            key=f"btn_{random.randint(1, 1000000)}",
            label="📥 Exporter en Excel",
            data=excel_file,
            file_name=f"excel_{random.randint(1,100000)}.pdf",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

# Fonction utilitaire pour convertir un DataFrame en Excel
def convert_df_to_excel(df):
    
    # Supprimer le fuseau horaire des colonnes datetime avec timezone
    df = df.copy()
    for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Activites')
        # Pas besoin de writer.save() dans un bloc `with`
    processed_data = output.getvalue()
    return processed_data

