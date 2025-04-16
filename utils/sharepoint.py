
import pandas as pd
import streamlit as st
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from io import StringIO

def fetch_from_sharepoint():
    url = "https://govmr.sharepoint.com/sites/Suivi-Evaluation/"
    list_name = "Suivi-des-activités 2025"
    ctx_auth = AuthenticationContext(url)
    ctx_auth.acquire_token_for_user(st.secrets["sharepoint"]["username"], st.secrets["sharepoint"]["password"])
    ctx = ClientContext(url, ctx_auth)
    target_list = ctx.web.lists.get_by_title(list_name)
    items = target_list.items.get().execute_query()

    data = []
    for item in items:
        data.append(item.properties)
    df = pd.DataFrame(data)
    return df
