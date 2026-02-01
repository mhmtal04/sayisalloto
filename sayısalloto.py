import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Master Analist v38.5", layout="wide")

# Tasarım CSS
st.markdown("""
    <style>
    .result-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0 25px 0; }
    .result-item {
        padding: 12px 18px; border-radius: 8px; font-weight: 600; font-size: 15px;
        display: flex; align-items: center; justify-content: center; min-width: 110px;
    }
    .ana-sayi { background-color: rgba(28, 131, 225, 0.1); color: rgb(0, 104, 201); border-left: 4px solid rgb(0, 104, 201); }
    .joker-sayi { background-color: rgba(255, 165, 0, 0.1); color: rgb(255, 140, 0); border-left: 4px solid rgb(255, 140, 0); }
    .super-sayi { background-color: rgba(255, 75, 75, 0.1); color: rgb(255, 75, 75); border-left: 4px solid rgb(255, 75, 75); }
    .stButton>button { width: 100%; background-color: #1c83e1; color: white; font-weight: bold; height: 3em; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Master Analist v38.5 - Spread & Markov Master")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # 1. SON ÇEKİLİŞ PANELİ
    last_draw = df.iloc[0]
    st.subheader(f"📅 Son Çekiliş: {last_draw['Tarih']}")
    res_html = '<div class="result-row">'
    for c in cols: res_html += f'<div class="result-item ana-sayi">{c}: {int(last_draw[c])}</div>'
    if 'Joker' in df.columns: res_html += f'<div class="result-item joker-sayi">Joker: {int(last_draw["Joker"])}</div>'
    if 'Super' in df.columns: res_html += f'<div class="result-item super-sayi">Super: {int(last_draw["Super"])}</div>'
    res_html += '</div>'
    st.markdown(res_html, unsafe_allow_html=True)

    # 2. VERİ ANALİZİ
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    draws_raw = df[cols].values
    draws = np.array([[int(x) for x in row if pd.notnull(x)] for row in draws_raw])

    last_seen = {n: i for i, d in enumerate(draws[::-1]) for n in d}
    co_matrix_global = np.zeros((91, 91))
    for d in draws:
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix_global[n1][n2] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}
    all_patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]
    all_parities = [tuple(['Tek' if n % 2 != 0 else 'Çift' for n in d]) for d in draws]

    def predict_next(history):
        last_s = history[0]
        succs = [history[i] for i in range(len(history)-1) if history[i+1] == last_s]
        return Counter(succs).most_common(1)[0][0] if succs else Counter(history).most_common(1)[0][0]

    pred_pattern = predict_next(all_patterns)
    pred_parity = predict_next(all_parities)

    # 3. MUHAKEME MOTORU (16,28,31... ODAKLI)
    def get_v38_score(n, pos_idx, current_res):
        reg_idx = np.digitize(n, custom_bins) - 1
        score = (pos_freq[cols[pos_idx]][n] * 0.4) + (last_seen.get(n, 0) * 0.1)
        
        if current_res:
            prev = current_res[-1]
            n1, n2 = sorted([n, prev])
            score += (co_matrix_global[n1][n2] * 2.5)
            
            # YAYILIM ANALİZİ: Dünkü sonucu (16-28-31) yakalamak için gap bonusu
            gap = n - prev
            if 8 <= gap <= 22: score += 150 
            if gap < 5: score -= 250 # Kümelenme cezası
            
            # BÖLGESEL YAYILIM: Onluk blokları homojen dağıtmaya zorla
            same_reg = sum(1 for s in current_res if (np.digitize(s, custom_bins)-1) == reg_idx)
            if same_reg >= 1: score -= 500 
        
        return score

    def make_col(offset):
        res = []
        req_regions = [i for i, count in enumerate(pred_pattern) for _ in range(count)]
        for i, reg_idx in enumerate(req_regions):
            start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
            cands = [n for n in range(start, end) if n not in res]
            cands.sort(key=lambda x: get_v38_score(x, i, res), reverse=True)
            if cands: res.append(cands[min(offset, len(cands)-1)])
        return sorted(res)

    # 4. ARAYÜZ ÜRETİM PANELİ
    st.divider()
    st.subheader("🔮 Stratejik Tahmin Üretici")
    c1, c2 = st.columns([1, 1])
    with c1:
        num_to_predict = st.slider("Üretilecek Kolon Sayısı", 1, 10, 3)
    with c2:
        st.write("##")
        generate_btn = st.button("🚀 Tahminleri Üret")

    if generate_btn:
        for i in range(num_to_predict):
            kolon = make_col(i)
            st.success(f"**Kolon {i+1}:** `{kolon}`")

    # 5. ANALİZ VE GRAFİKLER
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📈 En Popüler 5 Blok Dizilişi")
        p_labels = ["-".join(map(str, [x for x in p if x>0])) for p in all_patterns]
        st.bar_chart(pd.DataFrame(Counter(p_labels).most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))
    
    with g2:
        st.subheader("🔗 En Sinerjik İkililer (Global)")
        gp = [(f"{i}-{j}", int(co_matrix_global[i][j])) for i in range(1, 91) for j in range(i+1, 91) if co_matrix_global[i][j] > 10]
        st.table(pd.DataFrame(sorted(gp, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Frekans']))

    st.subheader("📍 Pozisyonel Liderler (Top 6)")
    pos_data = {c: [f"{num} ({count})" for num, count in pos_freq[c].most_common(6)] for c in cols}
    st.table(pd.DataFrame(pos_data))

else:
    st.info("Lütfen analiz için güncel loto.csv dosyasını yükleyin.")
