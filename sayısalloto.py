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
    .stNumberInput { width: 150px; }
    .stButton>button { background-color: #0083B8; color: white; border-radius: 10px; height: 3em; width: 100%; font-weight: bold; }
    .highlight { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 5px solid #0083B8; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ v36 Hyper-Logic: Görsel Muhakeme Sistemi")

uploaded_file = st.file_uploader("Veri Setini Yükle (loto.csv)", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    # Veriyi temizle ve sayıya çevir
    draws = df[cols].dropna().values.astype(int)
    
    # 1. TEMEL ANALİZ KATMANLARI
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    
    # Her pozisyonun (T1-T6) en çok çıkanları
    pos_freq = {c: Counter(df[c]) for c in cols}
    
    # Bekleme Süresi (Pusu)
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen: last_seen[n] = i

    # Sinerji Matrisi (Dünkü 28-31 kankalığı)
    co_matrix = np.zeros((91, 91))
    for d in draws[:150]:
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                co_matrix[n1][n2] += 1

    # Diziliş Analizi (Pattern)
    all_patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]
    pattern_counts = Counter(all_patterns)
    most_common_p = pattern_counts.most_common(1)[0][0]

    # --- ARAYÜZ GRAFİKLERİ ---
    st.divider()
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📊 Diziliş (Blok Yapısı) Dağılımı")
        p_df = pd.DataFrame([{"Diziliş": "-".join(map(str, [x for x in p if x>0])), "Adet": c} for p, c in pattern_counts.most_common(8)])
        st.bar_chart(p_df.set_index("Diziliş"))

    with g2:
        st.subheader("🔥 Momentum Isı Haritası")
        heat_data = np.zeros((9, 10))
        for n in range(1, 91):
            r, c = (n-1)//10, (n-1)%10
            heat_data[r, c] = Counter(draws[:30].flatten()).get(n, 0)
        fig, ax = plt.subplots(figsize=(8, 3.5))
        sns.heatmap(heat_data, cmap="YlOrRd", annot=False, cbar=False)
        st.pyplot(fig)

    # --- TABLOLAR ---
    st.divider()
    t1, t2, t3 = st.columns(3)
    with t1:
        st.subheader("📍 Pozisyon Liderleri")
        st.table(pd.DataFrame({c: [n for n, f in pos_freq[c].most_common(5)] for c in cols}))
    with t2:
        st.subheader("💤 Pusuda Bekleyenler")
        waiting_list = sorted([(n, last_seen.get(n, 0)) for n in range(1, 91)], key=lambda x: x[1], reverse=True)[:10]
        st.table(pd.DataFrame(waiting_list, columns=["Sayı", "Gecikme"]))
    with t3:
        st.subheader("🔗 En Güçlü Sinerjiler")
        sin_list = sorted([(f"{i}-{j}", int(co_matrix[i][j])) for i in range(1,91) for j in range(i+1,91) if co_matrix[i][j] > 8], key=lambda x: x[1], reverse=True)[:10]
        st.table(pd.DataFrame(sin_list, columns=["İkili", "Sıklık"]))

    # --- TAHMİN MOTORU ---
    st.divider()
    st.subheader("🔮 Hyper-Logic Tahmin Üretici")
    num_cols = st.number_input("Kaç adet tahmin üretilsin? (1-10)", 1, 10, 3)

    def get_v36_score(n, pos_idx, current_res):
        # 16, 28, 31, 41, 59, 74'ü yakalayan formül:
        m_puan = Counter(draws[:20].flatten()).get(n, 0) * 15.0 # Momentum
        s_puan = 0
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                s_puan += co_matrix[n1][n2] * 20.0 # Sinerji baskınlığı artırıldı
                # Mesafe Bonusu (Dünkü yayılım için kritik)
                if 10 <= abs(n - prev) <= 22: s_puan += 30
        
        p_puan = pos_freq[cols[pos_idx]][n] * 2.0 # Pozisyonel
        w_puan = last_seen.get(n, 0) * 1.2 # Pusu
        
        return m_puan + s_puan + p_puan + w_puan

    if st.button("Tahminleri Üret"):
        for i in range(num_cols):
            res = []
            # Dünkü 1-1-1-1-1-1 dizilişini baz alan akıllı yayılım
            target_p = most_common_p if i % 2 == 0 else (1,1,1,1,1,1,0,0,0)
            req_regions = [idx for idx, count in enumerate(target_p) for _ in range(count)]
            
            for idx, reg_idx in enumerate(req_regions):
                start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
                cands = [n for n in range(start, end) if n not in res]
                cands.sort(key=lambda x: get_v36_score(x, idx, res), reverse=True)
                if cands:
                    # Offset ile çeşitlilik sağla
                    pick = cands[min(i, len(cands)-1)]
                    res.append(pick)
            
            st.markdown(f"**Tahmin {i+1}:** `{sorted(res)}`", unsafe_allow_html=True)
