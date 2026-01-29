import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Zaman Ayarlı Master", layout="wide")

# Öngörü kutularını taklit eden yatay tasarım CSS
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

st.title("🛡️ Zaman Ayarlı Master Analist Botu")
st.markdown("Bot; 1. satırı **en güncel çekiliş** kabul ederek 'Kaç çekiliştir çıkmıyor?' hesabını buna göre yapar.")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # --- YENİ: SON ÇEKİLİŞ SONUÇLARI PANELİ ---
    last_draw = df.iloc[0]
    last_date = last_draw['Tarih'] if 'Tarih' in df.columns else "Bilinmiyor"
    
    st.subheader(f"📅 Son Çekiliş Sonuçları ({last_date})")
    res_html = '<div class="result-row">'
    for c in cols:
        res_html += f'<div class="result-item ana-sayi">{c}: {int(last_draw[c])}</div>'
    if 'Joker' in df.columns:
        res_html += f'<div class="result-item joker-sayi">Joker: {int(last_draw["Joker"])}</div>'
    if 'Super' in df.columns:
        res_html += f'<div class="result-item super-sayi">Super: {int(last_draw["Super"])}</div>'
    res_html += '</div>'
    st.markdown(res_html, unsafe_allow_html=True)
    st.divider()

    # 1. VERİ TEMİZLEME
    draws_raw = df[cols].values
    draws = []
    for row in draws_raw:
        clean_row = [int(x) for x in row if pd.notnull(x) and str(x).replace('.0','').isdigit()]
        if len(clean_row) == 6: draws.append(clean_row)
    draws = np.array(draws) 

    # 2. ANALİZ KATMANLARI
    co_matrix_global = np.zeros((91, 91))
    co_matrix_trend = np.zeros((91, 91))
    
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen:
                last_seen[n] = i

    for idx, d in enumerate(draws):
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if 0 < n1 < 91 and 0 < n2 < 91:
                    co_matrix_global[n1][n2] += 1
                    if idx < 50:
                        co_matrix_trend[n1][n2] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}
    
    def get_pattern(draw):
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)
    all_patterns = [get_pattern(d) for d in draws]

    # 3. MARKOV TAHMİNİ
    last_p = all_patterns[0]
    successors = [all_patterns[i] for i in range(len(all_patterns)-1) if all_patterns[i+1] == last_p]
    predicted_pattern = Counter(successors).most_common(1)[0][0] if successors else Counter(all_patterns).most_common(1)[0][0]

    # 4. MASTER MUHAKEME MOTORU
    def get_master_score(n, pos_idx, current_res):
        pos_name = cols[pos_idx]
        region_idx = (n-1) // 10
        score = (pos_freq[pos_name][n] * 0.4) + (last_seen.get(n, 0) * 0.1)
        
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                score += (co_matrix_global[n1][n2] * 1.0) + (co_matrix_trend[n1][n2] * 3.0)
                if last_seen.get(n, 0) > 20 and last_seen.get(prev, 0) > 20:
                    if co_matrix_global[n1][n2] > 5: score += 50
            
            same_reg = sum(1 for s in current_res if (s-1)//10 == region_idx)
            if same_reg >= 1:
                if np.sum([p[region_idx] for p in all_patterns[:15]]) > 4: score -= 250
        
        if np.sum(draws[:15] == n) >= 3: score -= 400
        return score

    def make_col(p, offset=0):
        res = []
        bins = [1, 11, 21, 31, 41, 51, 61, 71, 81, 91]
        for i, count in enumerate(p):
            if count > 0:
                cands = [n for n in range(bins[i], bins[i+1]) if n not in res]
                cands.sort(key=lambda x: get_master_score(x, i if i<6 else 5, res), reverse=True)
                res.extend(cands[offset : offset + count])
        return sorted(res[:6])

    # --- ARAYÜZ (Gelişmiş Analizler Alt Alta) ---
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("🔮 Öngörü")
        st.write(f"Tahmin Dizilişi: **{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}**")
        st.success(f"🥇 1. Kolon: `{make_col(predicted_pattern, 0)}`")
        st.info(f"🥈 2. Kolon: `{make_col(predicted_pattern, 2)}`")

    with c2:
        st.subheader("📍 Pozisyonel Liderler")
        pos_data = {c: [f"{num} ({count})" for num, count in pos_freq[c].most_common(5)] for c in cols}
        st.table(pd.DataFrame(pos_data))

    st.divider()
    t1, t2, t3 = st.columns(3)
    
    with t1:
        st.subheader("🔥 Moda")
        trend_pairs = [(f"{i}-{j}", int(co_matrix_trend[i][j])) for i in range(1,91) for j in range(i+1,91) if co_matrix_trend[i][j] > 0]
        st.table(pd.DataFrame(sorted(trend_pairs, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Trend']))

    with t2:
        st.subheader("🔗 Sinerji")
        global_p = [(f"{i}-{j}", int(co_matrix_global[i][j])) for i in range(1,91) for j in range(i+1,91) if co_matrix_global[i][j] > 8]
        st.table(pd.DataFrame(sorted(global_p, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Global']))

    with t3:
        st.subheader("💤 Pusu")
        pusu_list = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix_global[i][j] > 8:
                    ort_bekleme = (last_seen.get(i, 0) + last_seen.get(j, 0)) // 2
                    if ort_bekleme > 20:
                        pusu_list.append((f"{i}-{j}", int(co_matrix_global[i][j]), ort_bekleme))
        st.table(pd.DataFrame(sorted(pusu_list, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Güç', 'Çekiliş Önce']))
