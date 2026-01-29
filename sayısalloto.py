import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Full Master Suite", layout="wide")

st.title("🛡️ Full Master Analist Loto Botu")
st.markdown("Bot; **Trend (Son 50)**, **Pusu**, **Global Sinerji** ve **T-Bölgesi** analizlerinin tamamını kullanır.")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # 1. VERİ TEMİZLEME
    draws_raw = df[cols].values
    draws = []
    for row in draws_raw:
        clean_row = [int(x) for x in row if pd.notnull(x) and str(x).replace('.0','').isdigit()]
        if len(clean_row) == 6: draws.append(clean_row)
    draws = np.array(draws)

    # 2. DERİN ANALİZ KATMANLARI
    co_matrix_global = np.zeros((91, 91))
    co_matrix_trend = np.zeros((91, 91))
    for idx, d in enumerate(draws):
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = d[i], d[j]
                if 0 < n1 < 91 and 0 < n2 < 91:
                    co_matrix_global[n1][n2] += 1
                    co_matrix_global[n2][n1] += 1
                    if idx < 50: # Trend Analizi (Son 50)
                        co_matrix_trend[n1][n2] += 1
                        co_matrix_trend[n2][n1] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}
    last_seen = {n: i for i, d in enumerate(draws) for n in d}
    
    def get_pattern(draw):
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)
    all_patterns = [get_pattern(d) for d in draws]

    # 3. MARKOV TAHMİNİ
    last_p = all_patterns[0]
    successors = [all_patterns[i] for i in range(len(all_patterns)-1) if all_patterns[i+1] == last_p]
    predicted_pattern = Counter(successors).most_common(1)[0][0] if successors else Counter(all_patterns).most_common(1)[0][0]

    # 4. MUHAKEME MOTORU
    def get_master_score(n, pos_idx, current_res):
        pos_name = cols[pos_idx]
        region_idx = (n-1) // 10
        score = (pos_freq[pos_name][n] * 0.4) + (last_seen.get(n, 100) * 0.6)
        if current_res:
            for prev in current_res:
                score += (co_matrix_global[n][prev] * 1.0) + (co_matrix_trend[n][prev] * 3.0)
                if last_seen.get(n, 0) > 20 and last_seen.get(prev, 0) > 20:
                    if co_matrix_global[n][prev] > 5: score += co_matrix_global[n][prev] * 4.0
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

    # --- ARAYÜZ ---
    st.divider()
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("🔮 Stratejik Öngörü")
        st.write(f"Tahmin Edilen Diziliş: **{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}**")
        st.success(f"🥇 1. Kolon: `{make_col(predicted_pattern, 0)}`")
        st.info(f"🥈 2. Kolon: `{make_col(predicted_pattern, 2)}`")

    with c2:
        st.subheader("📍 Pozisyonel Liderler (T-Bölgesi)")
        pos_data = {c: [f"{num} ({count})" for num, count in pos_freq[c].most_common(5)] for c in cols}
        st.table(pd.DataFrame(pos_data))

    st.divider()
    st.subheader("📈 En Popüler 5 Diziliş")
    p_counts = Counter(["-".join(map(str, [x for x in p if x>0])) for p in all_patterns])
    st.bar_chart(pd.DataFrame(p_counts.most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))

    st.divider()
    t1, t2, t3 = st.columns(3)
    
    with t1:
        st.subheader("🔥 Son 50: Moda İkililer")
        trend_pairs = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix_trend[i][j] > 0:
                    trend_pairs.append((f"{i} - {j}", int(co_matrix_trend[i][j])))
        st.table(pd.DataFrame(sorted(trend_pairs, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Trend']))

    with t2:
        st.subheader("🔗 Genel Sinerji (Tüm Zamanlar)")
        global_pairs = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix_global[i][j] > 8:
                    global_pairs.append((f"{i} - {j}", int(co_matrix_global[i][j])))
        st.table(pd.DataFrame(sorted(global_pairs, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Global']))

    with t3:
        st.subheader("💤 Pusuda Bekleyenler")
        pusu_list = []
        for i in range(1, 91):
            for j in range(i+1, 91):
                if co_matrix_global[i][j] > 8:
                    soguk = (last_seen.get(i, 0) + last_seen.get(j, 0)) / 2
                    if soguk > 20:
                        pusu_list.append((f"{i} - {j}", int(co_matrix_global[i][j]), int(soguk)))
        st.table(pd.DataFrame(sorted(pusu_list, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Güç', 'Bekleme']))
