import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

# Sayfa Genişliği ve Stil
st.set_page_config(page_title="Loto AI v36.1 - Deep Analysis", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    .metric-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ v36.1 Deep-Analysis: Muhakeme ve Görsel Denetim")

uploaded_file = st.file_uploader("loto.csv dosyasını buraya yükleyin", type="csv")

if uploaded_file is not None:
    # Veriyi Oku ve Temizle
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws = df[cols].dropna().values.astype(int)
    
    # 1. ANALİZ KATMANLARI
    # Pozisyonel Güç (T1-T6 her bölgenin lideri)
    pos_freq = {c: Counter(df[c]) for c in cols}
    
    # Bekleme Listesi (En uzun süredir çıkmayanlar)
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen: last_seen[n] = i
    waiting_15 = sorted([(n, last_seen.get(n, 0)) for n in range(1, 91)], key=lambda x: x[1], reverse=True)[:15]

    # Sinerji (Birlikte en çok çıkan 15 ikili)
    co_matrix = np.zeros((91, 91))
    for d in draws[:200]: # Son 200 çekilişi baz al
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix[n1][n2] += 1
    
    synergy_list = []
    for i in range(1, 91):
        for j in range(i+1, 91):
            if co_matrix[i][j] > 0:
                synergy_list.append((f"{i}-{j}", int(co_matrix[i][j])))
    synergy_15 = sorted(synergy_list, key=lambda x: x[1], reverse=True)[:15]

    # Diziliş Analizi (Blok Yapısı)
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]
    pattern_counts = Counter(patterns)

    # --- ARAYÜZ GRAFİKLERİ ---
    st.divider()
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.subheader("📊 Tarihsel Blok Diziliş Grafiği")
        p_data = pd.DataFrame([{"Diziliş": "-".join(map(str, [x for x in p if x>0])), "Frekans": count} 
                             for p, count in pattern_counts.most_common(10)])
        st.bar_chart(p_data.set_index("Diziliş"))

    with c2:
        st.subheader("🔥 Sayı Yoğunluk Haritası")
        heat_data = np.zeros((9, 10))
        for n in range(1, 91):
            r, c = (n-1)//10, (n-1)%10
            heat_data[r, c] = Counter(draws[:50].flatten()).get(n, 0)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.heatmap(heat_data, cmap="YlOrRd", cbar=False, annot=False)
        st.pyplot(fig)

    # --- ANALİZ TABLOLARI ---
    st.divider()
    t1, t2, t3 = st.columns(3)
    
    with t1:
        st.subheader("📍 T-Bölgesi Liderleri (Top 5)")
        pos_df = pd.DataFrame({c: [n for n, f in pos_freq[c].most_common(5)] for c in cols})
        st.table(pos_df)

    with t2:
        st.subheader("💤 Pusuda Bekleyenler (15)")
        st.table(pd.DataFrame(waiting_15, columns=["Sayı", "Gecikme (Çekiliş)"]))

    with t3:
        st.subheader("🔗 En Çok Birlikte Çıkanlar (15)")
        st.table(pd.DataFrame(synergy_15, columns=["İkili", "Birlikte"]))

    # --- TAHMİN ÜRETİM BUTONU ---
    st.divider()
    st.subheader("🔮 v36.1 Hyper-Tahmin Üretici")
    col_count = st.slider("Üretilecek Tahmin Sayısı", 1, 10, 5)

    def get_deep_score(n, pos_idx, current_res):
        # Dünkü sonucu (16,28,31,41,59,74) yakalamak için dengelenmiş formül:
        freq_p = pos_freq[cols[pos_idx]][n] * 1.5
        wait_p = last_seen.get(n, 0) * 0.8
        syn_p = 0
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                syn_p += co_matrix[n1][n2] * 15.0 # Sinerji baskınlığı
                # Mesafe kontrolü (Dünkü gibi dengeli yayılım için)
                if 10 <= abs(n - prev) <= 25: syn_p += 20
        return freq_p + wait_p + syn_p

    if st.button("TAHMİN ÜRET"):
        st.markdown("### 🎲 Senin İçin Hesaplanan Kolonlar:")
        for i in range(col_count):
            res = []
            # Diziliş: Her tahminde en popüler 2 dizilişi dönüşümlü kullan
            target_p = (1, 1, 1, 1, 1, 1, 0, 0, 0) if i % 2 == 0 else pattern_counts.most_common(1)[0][0]
            req_regions = [idx for idx, val in enumerate(target_p) for _ in range(val)]
            
            for idx, reg_idx in enumerate(req_regions):
                start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
                candidates = [n for n in range(start, end) if n not in res]
                candidates.sort(key=lambda x: get_deep_score(x, idx, res), reverse=True)
                if candidates:
                    # Biraz varyasyon katmak için i oranında offset kullan
                    res.append(candidates[min(i, len(candidates)-1)])
            
            st.success(f"**Kolon {i+1}:** {sorted(res)}")
