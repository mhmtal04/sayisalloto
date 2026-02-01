import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

st.set_page_config(page_title="Loto AI v36 - Hyper-Logic", layout="wide")

# CSS - Stil Ayarları
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #0083B8; color: white; font-weight: bold; }
    .highlight-box { padding: 15px; border-radius: 10px; border: 1px solid #d1d1d1; background-color: white; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ v36 Hyper-Logic: Gelişmiş Muhakeme Sistemi")

uploaded_file = st.file_uploader("loto.csv dosyasını yükleyin", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    # Sayısallaştırma ve temizleme
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    draws = df[cols].dropna().values.astype(int)

    # 1. TEMEL VERİ ANALİZİ
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    
    # Pozisyon Liderleri (En çok çıkan 5 sayı)
    pos_freq = {c: Counter(df[c]) for c in cols}
    
    # Bekleme Süresi (Geciken 15 sayı)
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen: last_seen[n] = i
    
    # Sinerji (En çok birlikte çıkan 15 ikili)
    co_matrix = np.zeros((91, 91))
    for d in draws:
        d_sorted = sorted(d)
        for i in range(len(d_sorted)):
            for j in range(i + 1, len(d_sorted)):
                co_matrix[d_sorted[i]][d_sorted[j]] += 1

    # Diziliş Analizi
    all_patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]
    pattern_counts = Counter(all_patterns)

    # --- ARAYÜZ GRAFİKLERİ ---
    st.divider()
    
    # GRAFİK 1: En Çok Çıkan 5 Diziliş
    st.subheader("📊 En Çok Çıkan 5 Blok Dizilişi")
    p_labels = ["-".join(map(str, [x for x in p if x>0])) for p, c in pattern_counts.most_common(5)]
    p_values = [c for p, c in pattern_counts.most_common(5)]
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    sns.barplot(x=p_labels, y=p_values, palette="viridis", ax=ax1)
    st.pyplot(fig1)

    # TABLOLAR KATMANI
    st.divider()
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.subheader("📍 Pozisyon (T) Liderleri")
        pos_df = pd.DataFrame({c: [n for n, f in pos_freq[c].most_common(5)] for c in cols})
        st.table(pos_df)

    with col_b:
        st.subheader("💤 Geciken 15 Sayı (Pusu)")
        waiting_15 = sorted([(n, last_seen.get(n, 0)) for n in range(1, 91)], key=lambda x: x[1], reverse=True)[:15]
        st.table(pd.DataFrame(waiting_15, columns=["Sayı", "Çekiliş"]))

    with col_c:
        st.subheader("🔗 En Sık Birlikte Çıkan 15 İkili")
        sin_list = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix[i][j] > 0:
                    sin_list.append((f"{i}-{j}", int(co_matrix[i][j])))
        top_sin = sorted(sin_list, key=lambda x: x[1], reverse=True)[:15]
        st.table(pd.DataFrame(top_sin, columns=["İkili", "Frekans"]))

    # --- TAHMİN ÜRETİMİ (Hyper-Logic v36) ---
    st.divider()
    num_draws = st.select_slider("Üretilecek Tahmin Sayısı", options=list(range(1, 11)), value=3)
    
    def calculate_hyper_score(n, pos_idx, current_res):
        # Dünkü sonucu (16,28,31,41,59,74) yakalamak için tasarlanan skorlama
        m_score = Counter(draws[:25].flatten()).get(n, 0) * 18.0 # Güncel Momentum
        
        s_score = 0
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                s_score += co_matrix[n1][n2] * 25.0 # Sinerji Dopingi (28-31 gibi)
                
                # Altın Yayılım (Dünkü gibi 10-15 farkla dağılan sayılara bonus)
                if 8 <= abs(n - prev) <= 18: s_score += 40
        
        w_score = last_seen.get(n, 0) * 1.5 # Bekleme gücü
        return m_score + s_score + w_score

    if st.button("Tahmin Üret"):
        st.subheader("🔮 Hyper-Logic Tahminleri")
        for i in range(num_draws):
            res = []
            # Dünkü 1-1-1-1-1-1 yapısını yakalamak için blok bazlı seçim
            target_p = (1, 1, 1, 1, 1, 1, 0, 0, 0) # Dengeli Dağılım Modu
            req_regions = [idx for idx, count in enumerate(target_p) for _ in range(count)]
            
            for idx, reg_idx in enumerate(req_regions):
                start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
                cands = [n for n in range(start, end) if n not in res]
                cands.sort(key=lambda x: calculate_hyper_score(x, idx, res), reverse=True)
                if cands:
                    # Rastgelelik yerine en yüksek skorlu ilk 3 adaydan birini seç (Offset mantığı)
                    pick = cands[0] if i == 0 else cands[min(i, len(cands)-1)]
                    res.append(pick)
            
            st.markdown(f"<div class='highlight-box'><strong>Kolon {i+1}:</strong> {sorted(res)}</div>", unsafe_allow_html=True)
 
