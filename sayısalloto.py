import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

# Konfigürasyon
st.set_page_config(page_title="Loto AI v37 - Markov Master", layout="wide")

# CSS - v26 ve v32.5 Karışımı Premium Görünüm
st.markdown("""
    <style>
    .reportview-container { background: #f0f2f6; }
    .stButton>button { border-radius: 20px; background: linear-gradient(135deg, #0083B8 0%, #00B4DB 100%); color: white; font-weight: bold; }
    .last-draw-card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e1e4e8; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .number-circle { display: inline-block; width: 40px; height: 40px; background: #0083B8; color: white; border-radius: 50%; line-height: 40px; margin: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ v37 Markov-Momentum: Üst Düzey Muhakeme")

uploaded_file = st.file_uploader("Veri Setini Yükle (loto.csv)", type="csv")

if uploaded_file is not None:
    # Veri Hazırlama
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    data = df[cols].dropna().values.astype(int)
    
    # --- 1. SON ÇEKİLİŞ GÖSTERGESİ (v26 Özelliği) ---
    last_draw = data[0]
    st.markdown(f"""
    <div class="last-draw-card">
        <h3>📅 Son Çekiliş Sonucu ({df.iloc[0]['Tarih']})</h3>
        <div>
            {''.join([f'<div class="number-circle">{n}</div>' for n in last_draw])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. MARKOV ZİNCİRİ ANALİZİ (v26 Algoritması) ---
    # Onluk bloklar arası geçiş olasılıkları (0-8 arası bloklar)
    transitions = defaultdict(lambda: defaultdict(int))
    for draw in data:
        blocks = [n // 10 for n in draw]
        for i in range(len(blocks)-1):
            transitions[blocks[i]][blocks[i+1]] += 1
            
    # Olasılık matrisine çevir
    markov_matrix = {}
    for state, next_states in transitions.items():
        total = sum(next_states.values())
        markov_matrix[state] = {k: v/total for k, v in next_states.items()}

    # --- 3. İSTATİSTİKSEL KATMANLAR (v32.5 Özelliği) ---
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    pos_freq = {c: Counter(df[c]) for c in cols}
    
    # Bekleme süresi
    last_seen = {}
    for i, d in enumerate(data):
        for n in d:
            if n not in last_seen: last_seen[n] = i

    # Sinerji (Birlikte çıkma)
    co_matrix = np.zeros((91, 91))
    for d in data[:200]:
        for i in range(len(d)):
            for j in range(i+1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix[n1][n2] += 1

    # --- 4. GRAFİKLER ---
    st.divider()
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📊 En Çok Çıkan 5 Diziliş")
        patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in data]
        p_counts = Counter(patterns)
        p_df = pd.DataFrame([{"Diziliş": "-".join(map(str, [x for x in p if x>0])), "Frekans": c} for p, c in p_counts.most_common(5)])
        st.bar_chart(p_df.set_index("Diziliş"))

    with col_b:
        st.subheader("🔥 Markov Durum Geçiş Matrisi")
        m_map = np.zeros((9, 9))
        for i in range(9):
            for j in range(9):
                m_map[i, j] = markov_matrix.get(i, {}).get(j, 0)
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.heatmap(m_map, annot=False, cmap="Blues", ax=ax)
        st.pyplot(fig)

    # --- 5. ANALİZ TABLOLARI ---
    st.divider()
    t1, t2, t3 = st.columns(3)
    
    with t1:
        st.subheader("📍 Pozisyon Liderleri (Top 5)")
        st.table(pd.DataFrame({c: [n for n, f in pos_freq[c].most_common(5)] for c in cols}))
        
    with t2:
        st.subheader("💤 Uzun Süredir Çıkmayan 15 Sayı")
        pusu = sorted([(n, last_seen.get(n, 0)) for n in range(1, 91)], key=lambda x: x[1], reverse=True)[:15]
        st.table(pd.DataFrame(pusu, columns=["Sayı", "Gecikme"]))

    with t3:
        st.subheader("🔗 En Çok Birlikte Çıkan 15 İkili")
        sinerji_list = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix[i][j] > 0:
                    sinerji_list.append((f"{i}-{j}", int(co_matrix[i][j])))
        st.table(pd.DataFrame(sorted(sinerji_list, key=lambda x: x[1], reverse=True)[:15], columns=["İkili", "Sıklık"]))

    # --- 6. TAHMİN ÜRETİCİ (v37 Algoritması) ---
    st.divider()
    num_to_gen = st.slider("Üretilecek Tahmin Sayısı", 1, 10, 3)
    
    def markov_momentum_score(n, pos_idx, current_res):
        # 1. Markov Katmanı: Önceki sayının bloğundan bu sayının bloğuna geçiş şansı
        m_score = 0
        if current_res:
            prev_block = current_res[-1] // 10
            curr_block = n // 10
            m_score = markov_matrix.get(prev_block, {}).get(curr_block, 0) * 100
        
        # 2. Sinerji ve Momentum (Dünkü sonucu yakalayan v36 geliştirmesi)
        s_score = sum([co_matrix[sorted([n, p])[0]][sorted([n, p])[1]] for p in current_res]) * 15
        
        # 3. Pusu ve Frekans
        w_score = last_seen.get(n, 0) * 1.5
        f_score = pos_freq[cols[pos_idx]][n] * 0.5
        
        return m_score + s_score + w_score + f_score

    if st.button("🚀 Markov Tahmini Üret"):
        for i in range(num_to_gen):
            res = []
            # Diziliş: Her tahminde en popüler 5 dizilişten birini rastgele seç (Denge için)
            target_p = p_counts.most_common(5)[i % 5][0]
            req_blocks = [idx for idx, count in enumerate(target_p) for _ in range(count)]
            
            for idx, b_idx in enumerate(req_blocks):
                start, end = custom_bins[b_idx], custom_bins[b_idx+1]
                candidates = [n for n in range(start, end) if n not in res]
                candidates.sort(key=lambda x: markov_momentum_score(x, idx, res), reverse=True)
                if candidates:
                    # v26'nın meşhur "biraz rastgelelik ama mantıklı" dokunuşu
                    res.append(candidates[0]) 
            
            st.markdown(f"**Tahmin {i+1}:** `{sorted(res)}` (Markov Skoru Optimize Edildi)")
