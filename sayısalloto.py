import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

# Sayfa Genişliği ve Stil
st.set_page_config(page_title="Loto AI v35 - Muhakeme Merkezi", layout="wide")

st.title("🛡️ v35 Muhakeme Merkezi: Görsel Analiz ve Tahmin")

uploaded_file = st.file_uploader("loto.csv dosyasını yükleyin", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws = df[cols].values
    
    # 1. DİZİLİŞ TAHMİNİ (Pattern Recognition)
    # Onluk blok yapısı: 1-9, 10-19, 20-29...
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    
    def get_pattern(draw):
        return tuple(np.histogram(draw, bins=custom_bins)[0])

    all_patterns = [get_pattern(d) for d in draws if not np.isnan(d).any()]
    pattern_counts = Counter(all_patterns)
    
    # En muhtemel dizilişi bul (Dünkü 1-1-1-1-1-1 yapısı gibi)
    most_common_pattern = pattern_counts.most_common(1)[0][0]
    
    # --- GRAFİK 1: DİZİLİŞ FREKANSI ---
    st.subheader("📊 Tarihsel Diziliş (Blok Yapısı) Analizi")
    pattern_df = pd.DataFrame([
        {"Diziliş": "-".join(map(str, [x for x in p if x > 0])), "Adet": count} 
        for p, count in pattern_counts.most_common(10)
    ])
    st.bar_chart(pattern_df.set_index("Diziliş"))

    # 2. MUHAKEME GÜCÜ: MOMENTUM VE SINERJİ
    # Son 20 çekiliş momentumu
    recent_draws = draws[:20].flatten()
    recent_freq = Counter(recent_draws[~np.isnan(recent_draws)])
    
    # Sinerji Matrisi (Hangi sayılar birbirini çeker?)
    co_matrix = np.zeros((91, 91))
    for d in draws[:100]:
        d_clean = d[~np.isnan(d)]
        for i in range(len(d_clean)):
            for j in range(i + 1, len(d_clean)):
                n1, n2 = sorted([int(d_clean[i]), int(d_clean[j])])
                if n2 < 91: co_matrix[n1][n2] += 1

    # --- GRAFİK 2: ISI HARİTASI (Seaborn) ---
    st.subheader("🔥 Sayı Momentum Isı Haritası")
    heat_data = np.zeros((9, 10))
    for n in range(1, 91):
        r, c = (n-1)//10, (n-1)%10
        heat_data[r, c] = recent_freq.get(n, 0)
    
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(heat_data, annot=True, cmap="YlOrRd", ax=ax, 
                xticklabels=range(1, 11), yticklabels=[f"{i}0s" for i in range(9)])
    st.pyplot(fig)

    # 3. TAHMİN MOTORU (Muhakeme v35)
    def calculate_score(n, pos_idx, current_res):
        # Muhakeme bileşenleri
        m_score = recent_freq.get(n, 0) * 15.0  # Momentum (Son trendler)
        s_score = 0
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                s_score += co_matrix[n1][n2] * 10.0 # Sinerji (Kankalık)
        
        # Pusu Puanı (Dünkü 74 gibi geciken sayılar)
        dist_puan = 0
        if current_res:
            gap = abs(n - current_res[-1])
            if 10 <= gap <= 20: dist_puan = 25 # İdeal yayılım puanı
            
        return m_score + s_score + dist_puan

    def generate_final_col(pattern, offset=0):
        res = []
        req_regions = [i for i, count in enumerate(pattern) for _ in range(count)]
        for i, reg_idx in enumerate(req_regions):
            start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
            cands = [n for n in range(start, end) if n not in res]
            cands.sort(key=lambda x: calculate_score(x, i, res), reverse=True)
            if cands:
                idx = min(offset, len(cands)-1)
                res.append(cands[idx])
        return sorted(res)

    # --- SONUÇLAR ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"🥇 v35 Master Kolon: {generate_final_col(most_common_pattern, 0)}")
        st.info(f"🥈 v35 Alternatif: {generate_final_col(most_common_pattern, 1)}")
    with c2:
        st.write("🔍 **Muhakeme Analizi:**")
        st.write(f"- Tahmin Edilen Diziliş: **{'-'.join(map(str, [x for x in most_common_pattern if x>0]))}**")
        st.write("- Strateji: **Momentum + Yayılım Odaklı**")

