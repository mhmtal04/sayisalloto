import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

# Sayfa Ayarları
st.set_page_config(page_title="Loto AI v36 - Hyper-Logic", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #0083B8; color: white; font-weight: bold; }
    .result-card { padding: 15px; border-radius: 10px; border: 1px solid #ddd; background-color: white; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ v36 Hyper-Logic: Gelişmiş Muhakeme ve Tahmin")

uploaded_file = st.file_uploader("loto.csv dosyasını yükleyin", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws = df[cols].dropna().values.astype(int)
    
    # --- 1. VERİ ANALİZ KATMANLARI ---
    
    # Pozisyonel En Çok Çıkan 5 (T1-T6)
    pos_freq = {c: Counter(df[c]).most_common(5) for c in cols}
    
    # Uzun Zamandır Çıkmayan 15 Sayı (Pusu)
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen: last_seen[n] = i
    waiting_15 = sorted([(n, i) for n, i in last_seen.items()], key=lambda x: x[1], reverse=True)[:15]
    
    # En Çok Birlikte Çıkan 15 İkili (Sinerji)
    co_matrix = np.zeros((91, 91))
    for d in draws:
        d_sorted = sorted(d)
        for i in range(len(d_sorted)):
            for j in range(i + 1, len(d_sorted)):
                co_matrix[d_sorted[i]][d_sorted[j]] += 1
    
    sinerji_list = []
    for i in range(1, 91):
        for j in range(i+1, 91):
            if co_matrix[i][j] > 0:
                sinerji_list.append(((i, j), int(co_matrix[i][j])))
    top_sinerji_15 = sorted(sinerji_list, key=lambda x: x[1], reverse=True)[:15]

    # En Çok Çıkan 5 Diziliş (Pattern)
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    all_patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]
    top_patterns_5 = Counter(all_patterns).most_common(5)

    # --- 2. GÖRSEL ARAYÜZ (GRAFİKLER) ---
    
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 En Çok Çıkan 5 Diziliş")
        p_labels = ["-".join(map(str, [x for x in p[0] if x > 0])) for p in top_patterns_5]
        p_values = [p[1] for p in top_patterns_5]
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        sns.barplot(x=p_labels, y=p_values, palette="Blues_d", ax=ax1)
        st.pyplot(fig1)

    with col2:
        st.subheader("🔥 Sayıların Genel Sıcaklık Haritası")
        heat_map_data = np.zeros((9, 10))
        for n in range(1, 91):
            r, c = (n-1)//10, (n-1)%10
            heat_map_data[r, c] = Counter(draws.flatten()).get(n, 0)
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        sns.heatmap(heat_map_data, cmap="YlOrRd", annot=False, ax=ax2)
        st.pyplot(fig2)

    st.divider()
    t_col1, t_col2, t_col3 = st.columns(3)
    
    with t_col1:
        st.subheader("📍 T-Bölgesi Liderleri (Top 5)")
        st.table(pd.DataFrame({c: [f"{n} ({f})" for n, f in pos_freq[c]] for c in cols}))

    with t_col2:
        st.subheader("💤 Pusu: Bekleyen 15 Sayı")
        st.table(pd.DataFrame(waiting_15, columns=["Sayı", "Kaç Çekiliştir Yok"]))

    with t_col3:
        st.subheader("🔗 Sinerji: En Çok Birlikte Çıkan 15")
        st.table(pd.DataFrame([{"İkili": f"{k[0]}-{k[1]}", "Sıklık": v} for k, v in top_sinerji_15]))

    # --- 3. TAHMİN ÜRETİCİ ---
    st.divider()
    st.subheader("🔮 Hyper-Logic Tahmin Motoru")
    adet = st.number_input("Kaç kolon üretilsin?", 1, 10, 5)
    
    def get_v36_score(n, pos_idx, current_res):
        # Dünkü 16, 28, 31, 41, 59, 74'ü yakalamak için hibrit puanlama
        p_puan = dict(pos_freq[cols[pos_idx]]).get(n, 0) * 1.5
        w_puan = last_seen.get(n, 0) * 0.8 # Bekleme süresi ağırlığı
        
        # Sinerji (Birlikte çıkma) - En önemli bileşen
        s_puan = 0
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                s_puan += co_matrix[n1][n2] * 5.0 # Sinerji çarpanı
                # Yayılım Kontrolü: Ardışık sayılar arası 10-18 fark varsa dünkü gibi yayılır
                if 10 <= abs(n - prev) <= 18: s_puan += 20
        
        return p_puan + w_puan + s_puan

    if st.button("TAHMİN ÜRET"):
        st.write("### Üretilen Tahminler")
        for i in range(adet):
            res = []
            # Her kolon için farklı bir diziliş stratejisi (Dengeli Yayılım)
            target_p = top_patterns_5[i % 5][0]
            req_regions = [idx for idx, count in enumerate(target_p) for _ in range(count)]
            
            for idx, reg_idx in enumerate(req_regions):
                start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
                cands = [n for n in range(start, end) if n not in res]
                cands.sort(key=lambda x: get_v36_score(x, idx, res), reverse=True)
                if cands:
                    # Biraz varyasyon eklemek için i değerini offset olarak kullan
                    pick = cands[min(i, len(cands)-1)]
                    res.append(pick)
            
            st.markdown(f"<div class='result-card'><b>Kolon {i+1}:</b> <span style='color:#0083B8; font-size:18px;'>{sorted(res)}</span></div>", unsafe_allow_html=True)
