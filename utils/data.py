import streamlit as st
import pandas as pd
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

def load_data():

    # Lecture des secrets
    site_url = st.secrets["sharepoint"]["site_url"]
    username = st.secrets["sharepoint"]["username"]
    password = st.secrets["sharepoint"]["password"]
    list_name = st.secrets["sharepoint"]["list_name"]

    # Authentification
    ctx_auth = AuthenticationContext(site_url)
    if ctx_auth.acquire_token_for_user(username, password):
        ctx = ClientContext(site_url, ctx_auth)
        list_obj = ctx.web.lists.get_by_title(list_name)
        items = list_obj.items.get().execute_query()
        data = []
        for item in items:
            responsable_dict = item.properties.get("ResponsableId",{})
            #st.write(responsable_dict)
            if responsable_dict is not None and 0 in responsable_dict:
                responsable_id = responsable_dict[0]
            # else:
            #     st.write("responsable_dict est None ou ne contient pas la clé 0")
            #responsable_id=responsable_dict[int("0")]
            #st.write(responsable_id)
            user = ctx.web.get_user_by_id(responsable_id)
            ctx.load(user, ["Title", "Email"])
            ctx.execute_query()
            responsable=user.properties['Title']
            #st.write(responsable)
            data.append({
                "Responsable": responsable,
                "Domaine": item.properties.get("Title", ""),
                "Activité": item.properties.get("field_1", ""),
                "Tache": item.properties.get("field_3", ""),
                "Date limite": item.properties.get("field_5", ""),
                "Suivi des réalisations": item.properties.get("Suividesr_x00e9_alisations", ""),
                "Taux réalisation": item.properties.get("Tauxr_x00e9_alisation", 0),
                "Statut": item.properties.get("field_6", ""),
                
            })
        df = pd.DataFrame(data)
    else:
        st.error("Échec d’authentification SharePoint.")
        st.stop()
    
    return df

