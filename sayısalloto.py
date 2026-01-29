import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Master Analist v20", layout="wide")

st.title("🛡️ Master Analist - Tam Donanımlı Panel")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    # 0. VERİ OKUMA
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # Son çekiliş verileri (Dosyadaki ilk veri satırı)
    last_draw_data = df.iloc[0] 
    last_date = last_draw_data['Tarih'] if 'Tarih' in df.columns else "Bilinmiyor"

    # --- YATAY ESTETİK SONUÇ PANELİ ---
    st.subheader(f"📅 Son Çekiliş Sonuçları ({last_date})")
    res_cols = st.columns(8)
    
    # Ana Sayılar (Mavi Kutular)
    for i, c in enumerate(cols):
        res_cols[i].info(f"**{c}**\n\n# {int(last_draw_data[c])}")
    
    # Joker (Sarı Kutu)
    if 'Joker' in df.columns:
        res_cols[6].warning(f"**Joker**\n\n# {int(last_draw_data['Joker'])}")
        
    # Super (Kırmızı Kutu)
    if 'Super' in df.columns:
        res_cols[7].error(f"**Super**\n\n# {int(last_draw_data['Super'])}")
    
    st.divider()

    # 1. VERİ TEMİZLEME VE HAZIRLIK
    draws_raw = df[cols].values
    draws = []
    for row in draws_raw:
        clean_row = [int(x) for x in row if pd.notnull(x)]
        if len(clean_row) == 6: draws.append(clean_row)
    draws = np.array(draws) 

    # 2. ANALİZ MATRİSLERİ VE BEKLEME SÜRELERİ
    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen:
                last_seen[n] = i

    co_matrix_global = np.zeros((91, 91))
    co_matrix_trend = np.zeros((91, 91))
    for idx, d in enumerate(draws):
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = d[i], d[j]
                if 0 < n1 < 91 and 0 < n2 < 91:
                    co_matrix_global[n1][n2] += 1
                    co_matrix_global[n2][n1] += 1
                    if idx < 50: # Son 50 çekiliş trendi
                        co_matrix_trend[n1][n2] += 1
                        co_matrix_trend[n2][n1] += 1

    pos_freq = {c: Counter(df[c]) for c in cols}
    
    # Markov Örüntü Tahmini
    def get_pattern(draw):
        counts, _ = np.histogram(draw, bins=[1, 11, 21, 31, 41, 51, 61, 71, 81, 91])
        return tuple(counts)
    all_patterns = [get_pattern(d) for d in draws]
    last_p = all_patterns[0]
    successors = [all_patterns[i] for i in range(len(all_patterns)-1) if all_patterns[i+1] == last_p]
    predicted_pattern = Counter(successors).most_common(1)[0][0] if successors else Counter(all_patterns).most_common(1)[0][0]

    # 3. MUHAKEME VE KOLON ÜRETİMİ
    def get_master_score(n, pos_idx, current_res):
        pos_name = cols[pos_idx]
        score = (pos_freq[pos_name][n] * 0.4) + (last_seen.get(n, 0) * 0.1)
        if current_res:
            for prev in current_res:
                score += (co_matrix_global[n][prev] * 1.0) + (co_matrix_trend[n][prev] * 3.0)
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

    # --- ANA PANELLER ---
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("🔮 Öngörü ve Kolonlar")
        st.write(f"Tahmin Dizilişi: **{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}**")
        st.success(f"🥇 1. Kolon: `{make_col(predicted_pattern, 0)}`")
        st.info(f"🥈 2. Kolon: `{make_col(predicted_pattern, 2)}`")

    with c2:
        st.subheader("📍 Pozisyonel Liderler (T-Bölgesi)")
        pos_data = {c: [f"{num} ({count})" for num, count in pos_freq[c].most_common(5)] for c in cols}
        st.table(pd.DataFrame(pos_data))

    st.divider()
    st.subheader("📈 En Popüler 5 Diziliş Tipi")
    p_counts = Counter(["-".join(map(str, [x for x in p if x>0])) for p in all_patterns])
    st.bar_chart(pd.DataFrame(p_counts.most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))

    # --- ÜÇLÜ ANALİZ TABLOLARI (MODA, SİNERJİ, PUSU) ---
    st.divider()
    t1, t2, t3 = st.columns(3)
    
    with t1:
        st.subheader("🔥 Moda İkililer")
        trend_pairs = [(f"{i}-{j}", int(co_matrix_trend[i][j])) for i in range(1,91) for j in range(i+1,91) if co_matrix_trend[i][j] > 0]
        st.table(pd.DataFrame(sorted(trend_pairs, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Trend']))
        
    with t2:
        st.subheader("🔗 Genel Sinerji")
        global_p = [(f"{i}-{j}", int(co_matrix_global[i][j])) for i in range(1,91) for j in range(i+1,91) if co_matrix_global[i][j] > 8]
        st.table(pd.DataFrame(sorted(global_p, key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Global']))
        
    with t3:
        st.subheader("💤 Pusuda Bekleyenler")
        pusu_list = [(f"{i}-{j}", int(co_matrix_global[i][j]), (last_seen.get(i,0)+last_seen.get(j,0))//2) for i in range(1,91) for j in range(i+1,91) if co_matrix_global[i][j] > 8]
        # Beklemesi 20 çekilişten fazla olan, en güçlü 10 pusu ikilisi
        st.table(pd.DataFrame(sorted([p for p in pusu_list if p[2]>20], key=lambda x: x[1], reverse=True)[:10], columns=['İkili', 'Güç', 'Çekiliş Önce']))
