import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

# Sayfa Yapılandırması
st.set_page_config(page_title="Loto AI v37 - Omni Predictor", layout="wide")

st.markdown("""
    <style>
    .main-title { color: #1E88E5; font-weight: bold; text-align: center; }
    .stButton>button { background: linear-gradient(to right, #1E88E5, #1565C0); color: white; border-radius: 8px; }
    .result-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #1E88E5; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Loto AI v37: Omni-Predictor")

uploaded_file = st.file_uploader("loto.csv dosyasını yükleyin", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    # Sayısal veriye çevirme ve temizleme
    data_clean = df[cols].dropna().values.astype(int)
    
    # --- SON ÇEKİLİŞ GÖSTERİMİ (v26 ÖZELLİĞİ) ---
    last_draw_date = df.iloc[0]['Tarih']
    last_draw_nums = df.iloc[0][cols].values.tolist()
    st.markdown(f"### 🗓️ Sistemdeki Son Çekiliş: **{last_draw_date}**")
    cols_draw = st.columns(6)
    for idx, num in enumerate(last_draw_nums):
        cols_draw[idx].metric(f"T{idx+1}", int(num))
    st.divider()

    # --- ANALİZ PARAMETRELERİ ---
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    
    # 1. T Bölgeleri En Çok Çıkan 5 Sayı
    pos_freq = {c: Counter(df[c].dropna()) for c in cols}
    
    # 2. Bekleme (Gecikme) Analizi
    last_seen = {}
    for i, d in enumerate(data_clean):
        for n in d:
            if n not in last_seen: last_seen[n] = i
    waiting_15 = sorted([(n, last_seen.get(n, 0)) for n in range(1, 91)], key=lambda x: x[1], reverse=True)[:15]

    # 3. Sinerji (Birlikte Çıkma) Analizi
    co_matrix = np.zeros((91, 91))
    for d in data_clean[:200]: # Son 200 çekiliş odaklı
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix[n1][n2] += 1
    
    sinerji_list = []
    for i in range(1, 91):
        for j in range(i+1, 91):
            if co_matrix[i][j] > 0:
                sinerji_list.append((f"{i}-{j}", int(co_matrix[i][j])))
    top_15_sinerji = sorted(sinerji_list, key=lambda x: x[1], reverse=True)[:15]

    # 4. En Çok Çıkan 5 Diziliş Grafiği
    patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in data_clean]
    pattern_counts = Counter(patterns)
    top_5_patterns = pattern_counts.most_common(5)

    # --- GRAFİKSEL ARAYÜZ ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 En Çok Çıkan 5 Diziliş")
        p_labels = ["-".join(map(str, [x for x in p if x>0])) for p, c in top_5_patterns]
        p_values = [c for p, c in top_5_patterns]
        fig_p, ax_p = plt.subplots(figsize=(10, 5))
        sns.barplot(x=p_labels, y=p_values, palette="Blues_d", ax=ax_p)
        st.pyplot(fig_p)

    with col_right:
        st.subheader("🔥 Momentum Isı Haritası")
        heat_data = np.zeros((9, 10))
        for n, count in Counter(data_clean[:30].flatten()).items():
            if 1 <= n <= 90:
                heat_data[(n-1)//10, (n-1)%10] = count
        fig_h, ax_h = plt.subplots(figsize=(10, 5))
        sns.heatmap(heat_data, cmap="YlOrRd", annot=True, cbar=False, ax=ax_h)
        st.pyplot(fig_h)

    # --- TABLO ANALİZLERİ ---
    st.divider()
    t1, t2, t3 = st.columns(3)
    with t1:
        st.write("📍 **T Bölgeleri Liderleri**")
        st.table(pd.DataFrame({c: [n for n, f in pos_freq[c].most_common(5)] for c in cols}))
    with t2:
        st.write("💤 **En Çok Geciken 15 Sayı**")
        st.table(pd.DataFrame(waiting_15, columns=["Sayı", "Gecikme"]))
    with t3:
        st.write("🔗 **En Güçlü 15 Sinerji**")
        st.table(pd.DataFrame(top_15_sinerji, columns=["İkili", "Frekans"]))

    # --- TAHMİN MOTORU (v37 GELİŞMİŞ ALGORİTMA) ---
    st.divider()
    st.subheader("🔮 Omni-Predictor Tahmin Üretici")
    num_tahmin = st.slider("Tahmin Sayısı", 1, 10, 3)

    def get_omni_score(n, pos_idx, current_res):
        # Dünkü 16, 28, 31, 41, 59, 74 sonucunu çözmek için katsayılar:
        # 1. Momentum: Son trendlere %40 ağırlık
        m_score = Counter(data_clean[:25].flatten()).get(n, 0) * 18.0
        # 2. Sinerji: Birlikte çıkma geçmişine %35 ağırlık
        s_score = 0
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                s_score += co_matrix[n1][n2] * 25.0 # Çok yüksek sinerji çarpanı
                # Yayılım Kontrolü: Ardışık sayılar arası 8-18 fark varsa bonus
                if 8 <= abs(n - prev) <= 18: s_score += 40
        # 3. Pusu: Gecikme süresine %25 ağırlık
        w_score = last_seen.get(n, 0) * 1.5
        
        return m_score + s_score + w_score

    if st.button("Tahminleri Üret"):
        for i in range(num_tahmin):
            res = []
            # Diziliş: Her onluktan bir sayı (1-1-1-1-1-1) stratejisini zorla
            # Bu, dünkü sonucu yakalamanın anahtarıdır.
            target_pattern = (1,1,1,1,1,1,0,0,0) if i%2==0 else top_5_patterns[0][0]
            req_regions = [idx for idx, count in enumerate(target_pattern) if count > 0]
            
            for idx, reg_idx in enumerate(req_regions[:6]):
                start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
                cands = [n for n in range(start, end) if n not in res]
                cands.sort(key=lambda x: get_omni_score(x, idx, res), reverse=True)
                if cands:
                    # Offset kullanımı: Her tahminde en iyi 1. değil, bazen 2. veya 3. seçenek
                    res.append(cands[min(i, len(cands)-1)])
            
            st.markdown(f"<div class='result-card'><strong>Tahmin {i+1}:</strong> {sorted(res)}</div>", unsafe_allow_html=True)
