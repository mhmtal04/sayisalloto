import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Master Analist v21", layout="wide")

# CSS ile Kutuları Yan Yana Kilitleme ve Renklendirme
st.markdown("""
    <style>
    .loto-container {
        display: flex;
        flex-wrap: nowrap;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 20px;
    }
    .loto-box {
        flex: 1;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
        min-width: 80px;
    }
    .blue-box { background-color: #007bff; border: 2px solid #0056b3; }
    .orange-box { background-color: #fd7e14; border: 2px solid #d45d00; }
    .red-box { background-color: #dc3545; border: 2px solid #a71d2a; }
    .label { font-size: 0.8em; opacity: 0.9; display: block; margin-bottom: 5px; }
    .number { font-size: 1.8em; display: block; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Master Analist - Kesin Yatay Görünüm")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    last_draw = df.iloc[0]
    last_date = last_draw['Tarih'] if 'Tarih' in df.columns else "Bilinmiyor"

    # --- HTML TABANLI YATAY ŞERİT ---
    st.subheader(f"📅 Son Çekiliş Sonuçları ({last_date})")
    
    # Tüm sonuçları tek bir HTML satırında birleştiriyoruz
    loto_html = '<div class="loto-container">'
    for c in cols:
        loto_html += f'<div class="loto-box blue-box"><span class="label">{c}</span><span class="number">{int(last_draw[c])}</span></div>'
    
    if 'Joker' in df.columns:
        loto_html += f'<div class="loto-box orange-box"><span class="label">Joker</span><span class="number">{int(last_draw["Joker"])}</span></div>'
    
    if 'Super' in df.columns:
        loto_html += f'<div class="loto-box red-box"><span class="label">Super</span><span class="number">{int(last_draw["Super"])}</span></div>'
    
    loto_html += '</div>'
    st.markdown(loto_html, unsafe_allow_html=True)
    
    st.divider()

    # --- ANALİZ VE MUHAKEME BÖLÜMÜ ---
    draws = df[cols].dropna().astype(int).values
    last_seen = {n: i for i, d in enumerate(draws) for n in d}
    
    co_matrix_global = np.zeros((91, 91))
    co_matrix_trend = np.zeros((91, 91))
    for idx, d in enumerate(draws):
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = d[i], d[j]
                if 0 < n1 < 91 and 0 < n2 < 91:
                    co_matrix_global[n1][n2] += 1
                    co_matrix_global[n2][n1] += 1
                    if idx < 50:
                        co_matrix_trend[n1][n2] += 1
                        co_matrix_trend[n2][n1] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}
    
    def get_pattern(draw):
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)
    all_patterns = [get_pattern(d) for d in draws]
    predicted_pattern = Counter(all_patterns).most_common(1)[0][0]

    def get_master_score(n, pos_idx, current_res):
        score = (pos_freq[cols[pos_idx]][n] * 0.4) + (last_seen.get(n, 0) * 0.1)
        if current_res:
            for prev in current_res:
                score += (co_matrix_global[n][prev] * 1.0) + (co_matrix_trend[n][prev] * 3.0)
        return score

    def make_col(p, offset=0):
        res = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        for i, count in enumerate(p):
            if count > 0:
                cands = [n for n in range(bins[i], bins[i+1]) if n not in res]
                cands.sort(key=lambda x: get_master_score(x, i if i<6 else 5, res), reverse=True)
                res.extend(cands[offset : offset + count])
        return sorted(res[:6])

    # --- ALT PANELLER ---
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("🔮 Öngörü")
        st.success(f"🥇 1. Kolon: `{make_col(predicted_pattern, 0)}`")
        st.info(f"🥈 2. Kolon: `{make_col(predicted_pattern, 2)}`")

    with c2:
        st.subheader("📍 Pozisyonel Liderler")
        pos_data = {c: [f"{num} ({count})" for num, count in pos_freq[c].most_common(5)] for c in cols}
        st.table(pd.DataFrame(pos_data))

    st.divider()
    t1, t2, t3 = st.columns(3)
    with t1:
        st.subheader("🔥 Moda")
        tp = [(f"{i}-{j}", int(co_matrix_trend[i][j])) for i in range(1,91) for j in range(i+1,91) if co_matrix_trend[i][j] > 0]
        st.table(pd.DataFrame(sorted(tp, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Trend']))
    with t2:
        st.subheader("🔗 Sinerji")
        gp = [(f"{i}-{j}", int(co_matrix_global[i][j])) for i in range(1,91) for j in range(i+1,91) if co_matrix_global[i][j] > 8]
        st.table(pd.DataFrame(sorted(gp, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Global']))
    with t3:
        st.subheader("💤 Pusu")
        pl = [(f"{i}-{j}", int(co_matrix_global[i][j]), (last_seen.get(i,0)+last_seen.get(j,0))//2) for i in range(1,91) for j in range(i+1,91) if co_matrix_global[i][j] > 8]
        st.table(pd.DataFrame(sorted([p for p in pl if p[2]>20], key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Güç', 'Bekleme']))
