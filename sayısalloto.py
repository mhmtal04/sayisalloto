import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

st.set_page_config(page_title="Loto AI - v33 Isı Haritası & Sinerji", layout="wide")

# Tasarım CSS
st.markdown("""
    <style>
    .result-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0 25px 0; }
    .result-item {
        padding: 12px 18px; border-radius: 8px; font-weight: 600; font-size: 15px;
        display: flex; align-items: center; justify-content: center; min-width: 110px;
    }
    .ana-sayi { background-color: rgba(28, 131, 225, 0.1); color: rgb(0, 104, 201); border-left: 4px solid rgb(0, 104, 201); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ v33 - Isı Haritası & Sinerji Odaklı Muhakeme")

# Dosya Yükleme
uploaded_file = st.file_uploader("CSV Dosyasını Yükle (loto.csv)", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    draws_raw = df[cols].values
    draws = np.array([[int(x) for x in row if pd.notnull(x)] for row in draws_raw if len(row) >= 6])
    
    # 1. ISI HARİTASI (HEATMAP) - Sayıların Yoğunluk Analizi
    st.subheader("🔥 Sayı Yoğunluk Haritası (Son 50 Çekiliş)")
    heat_data = np.zeros((9, 10))
    # Son 50 çekilişteki tüm sayıları al
    last_50_flatten = draws[:50].flatten()
    for n in last_50_flatten:
        if 1 <= n <= 90:
            row, col = (n-1)//10, (n-1)%10
            heat_data[row, col] += 1
    
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(heat_data, annot=True, fmt=".0f", cmap="YlOrRd", ax=ax, 
                xticklabels=[str(i) for i in range(1, 11)], 
                yticklabels=[f"{i}0s" for i in range(9)])
    ax.set_title("Hangi Onluk Blok Daha Sıcak?")
    st.pyplot(fig)

    # 2. VERİ ANALİZİ (SINERJI & BEKLEME)
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen: last_seen[n] = i

    co_matrix = np.zeros((91, 91))
    for d in draws:
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix[n1][n2] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}
    
    def get_pattern(draw): return tuple(np.histogram(draw, bins=custom_bins)[0])
    all_patterns = [get_pattern(d) for d in draws]

    # Örüntü Tahmini
    def predict_pattern(history):
        last_s = history[0]
        succs = [history[i] for i in range(len(history)-1) if history[i+1] == last_s]
        return Counter(succs).most_common(1)[0][0] if succs else Counter(history).most_common(1)[0][0]

    pred_p = predict_pattern(all_patterns)

    # 3. SINERJİ ODAKLI SCORE MOTORU
    def get_v33_score(n, pos_idx, current_res):
        region_idx = np.digitize(n, custom_bins) - 1
        # Temel: Sıklık ve Bekleme
        score = (pos_freq[cols[pos_idx]][n] * 0.5) + (last_seen.get(n, 0) * 0.3)
        
        # --- SINERJI (v33 ANA ÖZELLİK) ---
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                # Sayılar arasındaki tarihsel bağı %500 daha fazla önemse
                score += (co_matrix[n1][n2] * 5.0)
        
        # Yüzdesel Fren (Doygunluk)
        count_last_15 = np.sum(draws[:15] == n)
        if count_last_15 >= 2: score *= 0.4
        
        return score

    # 4. KOLON ÜRETİMİ
    def make_v33_col(pattern, offset=0):
        res = []
        req_regions = [i for i, count in enumerate(pattern) for _ in range(count)]
        for i, reg_idx in enumerate(req_regions):
            start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
            cands = [n for n in range(start, end) if n not in res]
            cands.sort(key=lambda x: get_v33_score(x, i, res), reverse=True)
            if cands: res.append(cands[min(offset, len(cands)-1)])
        return sorted(res)

    # 5. ARAYÜZ GRAFİKLERİ VE SONUÇLAR
    st.divider()
    g1, g2 = st.columns([1.5, 1])
    
    with g1:
        st.subheader("🔮 v33 Master Tahminler")
        k1 = make_v33_col(pred_p, 0)
        k2 = make_v33_col(pred_p, 1)
        st.success(f"🥇 Master Kolon: `{k1}`")
        st.info(f"🥈 Alternatif Kolon: `{k2}`")
        st.write(f"Hedeflenen Blok Dizilişi: `{'-'.join(map(str, [x for x in pred_p if x>0]))}`")

    with g2:
        st.subheader("📈 En Çok Çıkan Dizilişler")
        p_labels = ["-".join(map(str, [x for x in p if x>0])) for p in all_patterns]
        st.bar_chart(pd.DataFrame(Counter(p_labels).most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))

    # ANALİZ TABLOLARI
    st.divider()
    t1, t2, t3 = st.columns(3)
    with t1:
        st.subheader("🔗 Sinerji Liderleri (Top 10)")
        sin_data = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix[i][j] > 10: sin_data.append((f"{i}-{j}", int(co_matrix[i][j])))
        st.table(pd.DataFrame(sorted(sin_data, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Birlikte Çıkma']))
        
    with t2:
        st.subheader("📍 Pozisyonel Güç (T1-T6)")
        pos_data = {c: [num for num, count in pos_freq[c].most_common(5)] for c in cols}
        st.table(pd.DataFrame(pos_data))
        
    with t3:
        st.subheader("💤 Bekleme (Pusu)")
        waiting_data = [(n, last_seen.get(n, 0)) for n in range(1, 91) if last_seen.get(n, 0) > 20]
        st.table(pd.DataFrame(sorted(waiting_data, key=lambda x: x[1], reverse=True)[:10], columns=['Sayı', 'Çekiliştir Çıkmıyor']))
