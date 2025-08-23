import streamlit as st
import pandas as pd
import re
import os
from io import BytesIO

st.set_page_config(page_title="Rekening Koran Converter", layout="wide")

def parse_txt_to_df(path: str, file_name: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    rows = []
    sub_comp = None

    for line in lines:
        # Cek SUB-COMP
        m_sc = re.search(r"SUB-COMP\s+(\d+)", line)
        if m_sc:
            sub_comp = m_sc.group(1)
            continue

        # Cek baris transaksi
        m = re.match(
            r"^\s*\d+\s+(\d{8,})\s+(.{1,24}?)\s+IDR\s+([\d\.,]+)\s+"
            r"(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2}:\d{2})\s+\S+\s+(.*\S)?\s*$",
            line
        )
        if not m:
            continue

        no_va  = m.group(1).strip()
        nama   = m.group(2).rstrip()
        amount = float(m.group(3).replace(",", ""))
        date   = m.group(4)
        time   = m.group(5)
        tail   = (m.group(6) or "")

        # Bersihkan tail (keterangan)
        tail = re.sub(r"\d+", " ", tail).replace("-", " ")
        tail = re.sub(r"\s+", " ", tail).strip()

        remark = f"{nama} {tail}".strip()

        rows.append([date, time, no_va, remark, amount, sub_comp, file_name])

    return pd.DataFrame(rows, columns=["DATE", "TIME", "NO.VA", "REMARK", "CREDIT", "SUBCOMPANY", "ASAL_FILE"])

st.title("📑 Rekening Koran TXT → Excel")

uploaded_files = st.file_uploader("Upload file TXT rekening koran", type="txt", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for uploaded in uploaded_files:
        # Simpan file sementara
        tmp_path = os.path.join("/tmp", uploaded.name)
        with open(tmp_path, "wb") as f:
            f.write(uploaded.read())
        df = parse_txt_to_df(tmp_path, uploaded.name)
        all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)

        st.success(f"Berhasil memproses {len(uploaded_files)} file. Total {len(final_df)} transaksi.")
        st.dataframe(final_df.head(20))

        # Simpan ke Excel di memory
        buffer = BytesIO()
        final_df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="⬇️ Download Excel",
            data=buffer,
            file_name="rekening_koran_all.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
