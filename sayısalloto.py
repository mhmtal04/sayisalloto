import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

# --- CONFIGURATION ---
st.set_page_config(page_title="Loto AI v38 - Hyper-Markov Master", layout="wide")

# --- CUSTOM CSS (V26 Standartları + Modern Dokunuş) ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-header { font-size: 36px; font-weight: bold; color: #1e3d59; text-align: center; margin-bottom: 20px; }
    .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #e0e0e0; }
    .last-draw-num { display: inline-block; width: 45px; height: 45px; background: #1e3d59; color: white; 
                    border-radius: 50%; line-height: 45px; text-align: center; margin: 5px; font-weight: bold; font-size: 18px; }
    .joker { background: #ff9800 !important; }
    .super { background: #f44336 !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background: linear-gradient(90deg, #1e3d59, #17b978); color: white; font-weight: bold; font-size: 18px; transition: 0.3s; border: none; }
    .stButton>button:hover { transform: scale(1.02); background: linear-gradient(90deg, #17b978, #1e3d59); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">🛡️ Loto AI v38 - Markov & Momentum Analyst</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("loto.csv dosyasını yükleyin", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    data_raw = df[cols].dropna().values.astype(int)
    
    # --- 1. SON ÇEKİLİŞ PANELİ ---
    last_row = df.iloc[0]
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(f"📅 Son Çekiliş: {last_row['Tarih']}")
    draw_html = '<div>'
    for c in cols: draw_html += f'<div class="last-draw-num">{int(last_row[c])}</div>'
    if 'Joker' in df.columns: draw_html += f'<div class="last-draw-num joker">{int(last_row["Joker"])}</div>'
    if 'Super' in df.columns: draw_html += f'<div class="last-draw-num super">{int(last_row["Super"])}</div>'
    draw_html += '</div></div>'
    st.markdown(draw_html, unsafe_allow_html=True)

    # --- 2. ANALİZ VE MARKOV HAZIRLIĞI ---
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    
    # Markov: Bloklar arası geçiş olasılığı (T_n block -> T_n+1 block)
    transitions = defaultdict(lambda: defaultdict(int))
    for draw in data_raw:
        blocks = [np.digitize(n, custom_bins) - 1 for n in draw]
        for i in range(len(blocks)-1):
            transitions[(i, blocks[i])][blocks[i+1]] += 1
            
    markov_prob = {}
    for state, next_states in transitions.items():
        total = sum(next_states.values())
        markov_prob[state] = {k: v/total for k, v in next_states.items()}

    # Sinerji (Together) & Pusu (Waiting)
    co_matrix = np.zeros((91, 91))
    for d in data_raw[:300]:
        for i in range(len(d)):
            for j in range(i+1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix[n1][n2] += 1

    last_seen = {}
    for i, d in enumerate(data_raw):
        for n in d:
            if n not in last_seen: last_seen[n] = i
    
    pos_freq = {c: Counter(df[c]) for c in cols}
    patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in data_raw]
    pattern_counts = Counter(patterns)

    # --- 3. GÖRSEL ANALİZ ---
    st.divider()
    st.subheader("📊 Stratejik Göstergeler")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**En Çok Çıkan 5 Blok Dizilişi**")
        p_labels = ["-".join(map(str, [x for x in p if x>0])) for p, c in pattern_counts.most_common(5)]
        p_values = [c for p, c in pattern_counts.most_common(5)]
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(x=p_labels, y=p_values, palette="viridis", ax=ax)
        st.pyplot(fig)

    with col_g2:
        st.markdown("**Pozisyonel Liderler (T1-T6 En Çok Çıkan 5)**")
        pos_df = pd.DataFrame({c: [n for n, f in pos_freq[c].most_common(5)] for c in cols})
        st.table(pos_df)

    st.divider()
    col_g3, col_g4 = st.columns(2)
    with col_g3:
        st.markdown("**💤 Pusuda Bekleyen 15 Sayı (En Büyük Gecikme)**")
        pusu_list = sorted([(n, last_seen.get(n, 0)) for n in range(1, 91)], key=lambda x: x[1], reverse=True)[:15]
        st.table(pd.DataFrame(pusu_list, columns=["Sayı", "Gecikme"]))

    with col_g4:
        st.markdown("**🔗 Sinerji: En Çok Birlikte Çıkan 15 İkili**")
        sin_pairs = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix[i][j] > 0: sin_pairs.append((f"{i}-{j}", int(co_matrix[i][j])))
        sin_pairs = sorted(sin_pairs, key=lambda x: x[1], reverse=True)[:15]
        st.table(pd.DataFrame(sin_pairs, columns=["İkili", "Frekans"]))

    # --- 4. MUHAKEME VE TAHMİN ---
    st.divider()
    st.subheader("🔮 Hyper-Markov Muhakeme Motoru")
    num_to_gen = st.slider("Tahmin Adedi (1-10)", 1, 10, 3)

    def get_v38_score(n, pos_idx, current_res):
        m_score = 0
        if current_res:
            prev_block = np.digitize(current_res[-1], custom_bins) - 1
            m_score = markov_prob.get((pos_idx-1, prev_block), {}).get(np.digitize(n, custom_bins)-1, 0) * 200
        
        s_score = sum([co_matrix[sorted([n, p])[0]][sorted([n, p])[1]] for p in current_res]) * 15
        w_score = last_seen.get(n, 0) * 2.5
        f_score = pos_freq[cols[pos_idx]][n] * 1.0
        
        # YAYILIM VE BLOK KONTROLÜ (Dünkü sonucu yakalamak için kritik)
        spread_score = 0
        if current_res:
            gap = n - current_res[-1]
            if 10 <= gap <= 25: spread_score = 70 # İdeal yayılım puanı
            if gap < 6: spread_score = -200 # Kümelenme cezası
            
        n_block = np.digitize(n, custom_bins) - 1
        if any((np.digitize(p, custom_bins)-1) == n_block for p in current_res):
            spread_score -= 150 # Blok doygunluğu cezası

        return m_score + s_score + w_score + f_score + spread_score

    if st.button("🚀 Tahminleri Üret"):
        for i in range(num_to_gen):
            res = []
            # Diziliş: Her onluktan bir sayı gelmesi durumu için bazen zorla (16,28,31... yapısı)
            target_p = pattern_counts.most_common(5)[i % 5][0]
            if i % 3 == 0: target_p = (0, 1, 1, 1, 1, 1, 0, 1, 0) # Mükemmel Yayılım Modu
            
            req_blocks = [idx for idx, count in enumerate(target_p) for _ in range(count)]
            for idx, b_idx in enumerate(req_blocks):
                start, end = custom_bins[b_idx], custom_bins[b_idx+1]
                cands = [n for n in range(start, end) if n not in res]
                if not cands: cands = [n for n in range(1, 91) if n not in res]
                cands.sort(key=lambda x: get_v38_score(x, idx, res), reverse=True)
                res.append(cands[min(i // 2, len(cands)-1)])
            
            st.success(f"**Tahmin {i+1}:** `{sorted(res)}` (Hyper-Spread Uyumlu)")
else:
    st.warning("Analiz başlatmak için lütfen CSV dosyasını yükleyin.")
