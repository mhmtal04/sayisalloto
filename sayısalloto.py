import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter, defaultdict

st.set_page_config(page_title="Loto AI - Master Analist v38", layout="wide")

# Tasarım CSS (V26 & v38 Standartları)
st.markdown("""
    <style>
    .result-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0 25px 0; }
    .result-item {
        padding: 12px 18px; border-radius: 8px; font-weight: 600; font-size: 15px;
        display: flex; align-items: center; justify-content: center; min-width: 110px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .ana-sayi { background-color: rgba(28, 131, 225, 0.1); color: rgb(0, 104, 201); border-left: 4px solid rgb(0, 104, 201); }
    .joker-sayi { background-color: rgba(255, 165, 0, 0.1); color: rgb(255, 140, 0); border-left: 4px solid rgb(255, 140, 0); }
    .super-sayi { background-color: rgba(255, 75, 75, 0.1); color: rgb(255, 75, 75); border-left: 4px solid rgb(255, 75, 75); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Master Analist v38 - Hyper-Markov Master")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle (loto.csv)", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # 1. SON ÇEKİLİŞ PANELİ
    last_draw = df.iloc[0]
    st.subheader(f"📅 Son Çekiliş Analizi: {last_draw['Tarih']}")
    res_html = '<div class="result-row">'
    for c in cols: res_html += f'<div class="result-item ana-sayi">{c}: {int(last_draw[c])}</div>'
    if 'Joker' in df.columns: res_html += f'<div class="result-item joker-sayi">Joker: {int(last_draw["Joker"])}</div>'
    res_html += '</div>'
    st.markdown(res_html, unsafe_allow_html=True)

    # 2. VERİ HAZIRLIĞI (v38 Logic)
    custom_bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]
    draws_raw = df[cols].values
    draws = np.array([[int(x) for x in row if pd.notnull(x)] for row in draws_raw])

    last_seen = {n: i for i, d in enumerate(draws[::-1]) for n in d} # Gecikme
    pos_freq = {c: Counter(df[c]) for c in cols}
    
    # Sinerji Matrisleri
    co_matrix_global = np.zeros((91, 91))
    for d in draws:
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix_global[n1][n2] += 1

    # 3. v38 HYPER-MUHAKEME MOTORU
    def get_v38_score(n, pos_idx, current_res):
        region_idx = np.digitize(n, custom_bins) - 1
        # Temel Frekans ve Gecikme Puanı
        score = (pos_freq[cols[pos_idx]][n] * 0.5) + (last_seen.get(n, 0) * 0.3)
        
        if current_res:
            prev = current_res[-1]
            n1, n2 = sorted([n, prev])
            # Sinerji Katkısı
            score += (co_matrix_global[n1][n2] * 2.0)
            
            # YAYILIM BONUSU (16,28,31 tipindeki homojen dağılımı yakalar)
            gap = n - prev
            if 8 <= gap <= 20: score += 100 
            if gap < 5: score -= 150 # Kümelenme cezası
            
            # BLOK DOYGUNLUK FRENİ (Aynı onlukta ikinci sayıya ceza)
            same_reg_count = sum(1 for s in current_res if (np.digitize(s, custom_bins)-1) == region_idx)
            if same_reg_count >= 1: score -= 300
            
        return score

    # Tahmin Üretim Fonksiyonu
    def predict_v38_col(offset=0):
        # En popüler örüntüleri (1-1-1-1-1-1 gibi) analiz et
        patterns = [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]
        best_pattern = Counter(patterns).most_common(5)[offset % 5][0]
        
        res = []
        req_regions = [i for i, count in enumerate(best_pattern) for _ in range(count)]
        
        for i, reg_idx in enumerate(req_regions):
            start, end = custom_bins[reg_idx], custom_bins[reg_idx+1]
            cands = [n for n in range(start, end) if n not in res]
            if not cands: cands = [n for n in range(1, 91) if n not in res]
            
            cands.sort(key=lambda x: get_v38_score(x, i, res), reverse=True)
            res.append(cands[min(offset, len(cands)-1)])
        return sorted(res)

    # 4. ARAYÜZ ÇIKTILARI
    st.divider()
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("🔮 Hyper-Markov Öngörüsü")
        k1 = predict_v38_col(0)
        st.success(f"🥇 Master Kolon (v38): `{k1}`")
        k2 = predict_v38_col(1)
        st.info(f"🥈 Alternatif Kolon: `{k2}`")
        st.warning("ℹ️ v38: Blok yayılımı ve homojen boşluk analizi aktif.")

    with c2:
        st.subheader("📍 Pozisyonel Liderler (Frekans)")
        pos_data = {c: [f"{num} ({count})" for num, count in pos_freq[c].most_common(5)] for c in cols}
        st.table(pd.DataFrame(pos_data))

    # ANALİZ TABLOLARI
    st.divider()
    t1, t2, t3 = st.columns(3)
    with t1:
        st.subheader("🔥 En Sinerjik İkililer")
        gp = [(f"{i}-{j}", int(co_matrix_global[i][j])) for i in range(1, 91) for j in range(i+1, 91) if co_matrix_global[i][j] > 10]
        st.table(pd.DataFrame(sorted(gp, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Frekans']))
    with t2:
        st.subheader("💤 Pusu 15 (En Gecikenler)")
        pusu = sorted([(n, last_seen.get(n, 0)) for n in range(1,91)], key=lambda x: x[1], reverse=True)[:10]
        st.table(pd.DataFrame(pusu, columns=['Sayı', 'Gecikme']))
    with t3:
        st.subheader("📈 En Popüler Blok Yapıları")
        patterns = ["-".join(map(str, [x for x in p if x>0])) for p in [tuple(np.histogram(d, bins=custom_bins)[0]) for d in draws]]
        st.table(pd.DataFrame(Counter(patterns).most_common(10), columns=['Diziliş', 'Adet']))

else:
    st.info("Lütfen analiz için güncel loto.csv dosyasını yükleyin.")
