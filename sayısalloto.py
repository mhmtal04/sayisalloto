import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

st.set_page_config(page_title="Loto AI - v34 Momentum Analist", layout="wide")

# Gereksinimler Hatırlatıcı (requirements.txt: streamlit, pandas, numpy, seaborn, matplotlib)

st.title("🛡️ v34 - Momentum & Trend Analist")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle (loto.csv)", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws_raw = df[cols].values
    draws = np.array([[int(x) for x in row if pd.notnull(x)] for row in draws_raw if len(row) >= 6])
    
    # --- 1. MOMENTUM ANALİZİ (Son 20 Çekiliş) ---
    recent_draws = draws[:20]
    recent_freq = Counter(recent_draws.flatten())
    
    # --- 2. ISI HARİTASI ---
    st.subheader("🔥 Momentum Isı Haritası (Güncel Form Durumu)")
    heat_data = np.zeros((9, 10))
    for n, count in recent_freq.items():
        if 1 <= n <= 90:
            row, col = (n-1)//10, (n-1)%10
            heat_data[row, col] = count
    
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(heat_data, annot=True, cmap="YlGnBu", ax=ax)
    st.pyplot(fig)

    # --- 3. MUHAKEME MOTORU (v34 Momentum Ağırlıklı) ---
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    last_seen = {n: i for i, d in enumerate(draws) for n in d if n not in last_seen}
    # (Hata düzeltmesi: last_seen döngüsü v32.1'deki gibi olmalı)
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen: last_seen[n] = i

    co_matrix = np.zeros((91, 91))
    for d in draws[:100]:
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                co_matrix[n1][n2] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}

    def get_v34_score(n, pos_idx, current_res):
        # %50 Momentum (Yeni!) + %20 Tarihsel + %30 Bekleme
        m_score = recent_freq.get(n, 0) * 10.0
        h_score = pos_freq[cols[pos_idx]][n] * 1.5
        w_score = last_seen.get(n, 0) * 0.5
        
        total_score = m_score + h_score + w_score
        
        # Sinerji (Önceki sayıyla uyum)
        if current_res:
            prev = current_res[-1]
            n1, n2 = sorted([n, prev])
            total_score += co_matrix[n1][n2] * 4.0
            
            # Yayılım Bonusu: Dünkü 16-28-31 gibi ideal boşluklara puan
            gap = abs(n - prev)
            if 10 <= gap <= 18: total_score += 15 # İdeal onluk atlama puanı
            
        return total_score

    # --- 4. TAHMİN ÜRETİMİ ---
    all_patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]
    def predict_pattern(history):
        last_s = history[0]
        succs = [history[i] for i in range(len(history)-1) if history[i+1] == last_s]
        return Counter(succs).most_common(1)[0][0] if succs else Counter(history).most_common(1)[0][0]
    
    pred_p = predict_pattern(all_patterns)

    def make_momentum_col(pattern, offset=0):
        res = []
        req_regions = [i for i, count in enumerate(pattern) for _ in range(count)]
        for i, reg_idx in enumerate(req_regions):
            start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
            cands = [n for n in range(start, end) if n not in res]
            # Momentum skoruna göre sırala
            cands.sort(key=lambda x: get_v34_score(x, i, res), reverse=True)
            if cands:
                res.append(cands[min(offset, len(cands)-1)])
        return sorted(res)

    # --- 5. SONUÇLAR ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🥇 v34 Master (Trend Odaklı)")
        st.success(f"Kolon 1: `{make_momentum_col(pred_p, 0)}`")
        st.info(f"Kolon 2: `{make_momentum_col(pred_p, 2)}`") # Offset 2 ile sürpriz kovala
        st.write(f"Diziliş: {pred_p}")
    
    with c2:
        st.subheader("🚀 Güncel Formda Olanlar (Son 20)")
        top_recent = [f"{n} ({c})" for n, c in recent_freq.most_common(10)]
        st.write(", ".join(top_recent))
