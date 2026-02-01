import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Master Analist v38", layout="wide")

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
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Master Analist v38 - Hyper-Logic & Yayılım")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # 1. SON ÇEKİLİŞ PANELİ (Super Sayısı Dahil)
    last_draw = df.iloc[0]
    st.subheader(f"📅 Son Çekiliş: {last_draw['Tarih'] if 'Tarih' in df.columns else 'Bilinmiyor'}")
    res_html = '<div class="result-row">'
    for c in cols: res_html += f'<div class="result-item ana-sayi">{c}: {int(last_draw[c])}</div>'
    if 'Joker' in df.columns: res_html += f'<div class="result-item joker-sayi">Joker: {int(last_draw["Joker"])}</div>'
    if 'Super' in df.columns: res_html += f'<div class="result-item super-sayi">Super: {int(last_draw["Super"])}</div>'
    res_html += '</div>'
    st.markdown(res_html, unsafe_allow_html=True)

    # 2. VERİ ANALİZİ & BLOKLAR
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    draws_raw = df[cols].values
    draws = np.array([[int(x) for x in row if pd.notnull(x)] for row in draws_raw if len(row) >= 6])

    last_seen = {n: i for i, d in enumerate(draws) for n in d}
    co_matrix_global = np.zeros((91, 91))
    for d in draws:
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix_global[n1][n2] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}
    all_patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]
    all_parities = [tuple(['Tek' if n % 2 != 0 else 'Çift' for n in d]) for d in draws]

    # Markov Öngörüleri
    def predict_next(history):
        last_s = history[0]
        succs = [history[i] for i in range(len(history)-1) if history[i+1] == last_s]
        return Counter(succs).most_common(1)[0][0] if succs else Counter(history).most_common(1)[0][0]

    predicted_pattern = predict_next(all_patterns)
    predicted_parity = predict_next(all_parities)

    # 3. v38 MUHAKEME MOTORU (16,28,31,41,59,74 YAKALAYICI)
    def get_master_score(n, pos_idx, current_res):
        region_idx = np.digitize(n, custom_bins) - 1
        score = (pos_freq[cols[pos_idx]][n] * 0.4) + (last_seen.get(n, 0) * 0.2)
        
        if current_res:
            prev = current_res[-1]
            n1, n2 = sorted([n, prev])
            score += (co_matrix_global[n1][n2] * 2.5)
            
            # GAP LOGIC: Dünkü sonucu yakalamak için en kritik yer
            gap = n - prev
            if 9 <= gap <= 21: score += 150 # 16->28, 41->59 gibi geçişleri ödüllendir
            if gap < 6: score -= 300 # Kümelenme varsa engelle
            
            # BLOK YAYILIM: Her onluktan maksimum 1 sayı
            same_reg = sum(1 for s in current_res if (np.digitize(s, custom_bins)-1) == region_idx)
            if same_reg >= 1: score -= 500
            
        return score

    def make_unified_col(pattern, parity_map, offset=0):
        res = []
        required_regions = [i for i, count in enumerate(pattern) for _ in range(count)]
        for i, reg_idx in enumerate(required_regions):
            target_p = parity_map[i] if i < len(parity_map) else 'Tek'
            start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
            cands = [n for n in range(start, end) if n not in res]
            final_pool = [n for n in cands if ('Tek' if n % 2 != 0 else 'Çift') == target_p]
            if not final_pool: final_pool = cands
            final_pool.sort(key=lambda x: get_master_score(x, i, res), reverse=True)
            if final_pool: res.append(final_pool[min(offset, len(final_pool)-1)])
        return sorted(res)

    # 4. ARAYÜZ & TAHMİN BUTONU
    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("🔮 Stratejik Tahmin Üretici")
        num_tahmin = st.slider("Tahmin Sayısı Seçin", 1, 10, 5)
        if st.button(f"{num_tahmin} Adet Tahmin Üret"):
            for i in range(num_tahmin):
                kolon = make_unified_col(predicted_pattern, predicted_parity, i)
                st.success(f"Kolon {i+1}: `{kolon}`")

    with c2:
        st.subheader("📈 En Popüler 5 Diziliş (Blok)")
        p_labels = ["-".join(map(str, [x for x in p if x>0])) for p in all_patterns]
        st.bar_chart(pd.DataFrame(Counter(p_labels).most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))

    # ANALİZ TABLOLARI
    st.divider()
    t1, t2, t3 = st.columns(3)
    with t1:
        st.subheader("🔗 Sinerji (Global)")
        gp = [(f"{i}-{j}", int(co_matrix_global[i][j])) for i in range(1, 91) for j in range(i+1, 91) if co_matrix_global[i][j] > 5]
        st.table(pd.DataFrame(sorted(gp, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Güç']))
    with t2:
        st.subheader("📍 Pozisyonel Liderler")
        st.table(pd.DataFrame({c: [n for n, f in pos_freq[c].most_common(5)] for c in cols}))
    with t3:
        st.subheader("💤 Pusu (Bekleyenler)")
        pusu = sorted([(n, last_seen.get(n, 0)) for n in range(1, 91)], key=lambda x: x[1], reverse=True)[:10]
        st.table(pd.DataFrame(pusu, columns=['Sayı', 'Gecikme']))

else:
    st.info("Lütfen loto.csv dosyasını yükleyin.")
