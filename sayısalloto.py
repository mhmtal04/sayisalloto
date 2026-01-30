import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter

st.set_page_config(page_title="Loto AI - Master Analist v29", layout="wide")

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

st.title("🛡️ Master Analist v29 - Parite Örüntü Motoru")

uploaded_file = st.file_uploader("CSV Dosyasını Yükle", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
    
    # 1. SON ÇEKİLİŞ PANELİ (Süper Sayı Sabitlendi)
    last_draw = df.iloc[0]
    st.subheader(f"📅 Son Çekiliş: {last_draw['Tarih'] if 'Tarih' in df.columns else 'Bilinmiyor'}")
    res_html = '<div class="result-row">'
    for c in cols: res_html += f'<div class="result-item ana-sayi">{c}: {int(last_draw[c])}</div>'
    if 'Joker' in df.columns: res_html += f'<div class="result-item joker-sayi">Joker: {int(last_draw["Joker"])}</div>'
    if 'Super' in df.columns: res_html += f'<div class="result-item super-sayi">Super: {int(last_draw["Super"])}</div>'
    res_html += '</div>'
    st.markdown(res_html, unsafe_allow_html=True)

    # 2. VERİ HAZIRLIĞI VE ANALİZ (KALİBRE EDİLMİŞ BİNLER)
    draws_raw = df[cols].values
    draws = np.array([[int(x) for x in row if pd.notnull(x)] for row in draws_raw if len(row) >= 6])
    
    # Blok Sınırları Yenilendi: 1-9, 10-19, 20-29... (18 ve 20 artık farklı bloklarda)
    bins = [1, 10, 20, 30, 40, 50, 60, 70, 80, 91]

    last_seen = {}
    for i, d in enumerate(draws):
        for n in d:
            if n not in last_seen: last_seen[n] = i

    co_matrix_global = np.zeros((91, 91))
    for idx, d in enumerate(draws):
        for i in range(len(d)):
            for j in range(i + 1, len(d)):
                n1, n2 = sorted([d[i], d[j]])
                if n2 < 91: co_matrix_global[n1][n2] += 1

    # POZİSYONEL PARİTE ANALİZİ (YENİ ÖZELLİK)
    pos_parity_freq = {c: Counter(['Tek' if n % 2 != 0 else 'Çift' for n in df[c]]) for c in cols}
    
    def get_pattern(draw): return tuple(np.histogram(draw, bins=bins)[0])
    def get_parity(draw): return tuple(['Tek' if n % 2 != 0 else 'Çift' for n in draw])

    all_patterns = [get_pattern(d) for d in draws]
    all_parities = [get_parity(d) for d in draws]

    # Örüntü Tahmin (Markov)
    def predict_next(history):
        last_s = history[0]
        succs = [history[i] for i in range(len(history)-1) if history[i+1] == last_s]
        return Counter(succs).most_common(1)[0][0] if succs else Counter(history).most_common(1)[0][0]

    predicted_pattern = predict_next(all_patterns)
    predicted_parity = predict_next(all_parities)

    # 3. MUHAKEME MOTORU (V26 Sadık + Birleşik Filtre)
    def get_master_score(n, pos_idx, current_res):
        score = (Counter(df[cols[pos_idx]])[n] * 0.4) + (last_seen.get(n, 0) * 0.1)
        if current_res:
            for prev in current_res:
                n1, n2 = sorted([n, prev])
                score += (co_matrix_global[n1][n2] * 1.5)
            # Bölgesel Fren (V26)
            reg = np.digitize(n, bins) - 1
            if sum(1 for s in current_res if (np.digitize(s, bins)-1) == reg) >= 1:
                score -= 250
        # Doygunluk Freni (V26)
        if np.sum(draws[:15] == n) >= 3: score -= 400
        return score

    # YAPBOZ BİRLEŞTİRME (Unified Logic)
    def make_unified_col(pattern, parity_map, offset=0):
        res = []
        req_bins = []
        for i, count in enumerate(pattern):
            for _ in range(count): req_bins.append(i)
        
        for i, b_idx in enumerate(req_bins):
            target_p = parity_map[i]
            # Sadece ilgili bloktaki ve doğru paritedeki sayıları filtrele
            cands = [n for n in range(bins[b_idx], bins[b_idx+1]) if n not in res]
            strict = [n for n in cands if ('Tek' if n % 2 != 0 else 'Çift') == target_p]
            
            final_list = strict if strict else cands
            final_list.sort(key=lambda x: get_master_score(x, i, res), reverse=True)
            if final_list:
                res.append(final_list[min(offset, len(final_list)-1)])
        return sorted(res)

    # 4. ARAYÜZ
    st.divider()
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.subheader("🔮 Birleşik Muhakeme (Yapboz)")
        st.write(f"Tahmin Blok Yapısı: `{'-'.join(map(str, [x for x in predicted_pattern if x>0]))}`")
        st.write(f"Tahmin Parite Akışı: `{'-'.join([p[0] for p in predicted_parity])}`")
        
        k1 = make_unified_col(predicted_pattern, predicted_parity, 0)
        k2 = make_unified_col(predicted_pattern, predicted_parity, 1)
        
        st.success(f"🥇 Master Kolon: `{k1}`")
        st.info(f"🥈 Alternatif Kolon: `{k2}`")

    with c2:
        st.subheader("📊 Pozisyonel Parite Analizi")
        parity_df = pd.DataFrame({c: [f"Tek: {pos_parity_freq[c]['Tek']}", f"Çift: {pos_parity_freq[c]['Çift']}"] for c in cols}, index=['Sıklık', 'Sıklık '])
        st.table(parity_df)

    # GRAFİKLER
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📈 Popüler Blok Dizilişleri")
        p_labels = ["-".join(map(str, [x for x in p if x>0])) for p in all_patterns]
        st.bar_chart(pd.DataFrame(Counter(p_labels).most_common(5), columns=['Diziliş', 'Adet']).set_index('Diziliş'))
    with g2:
        st.subheader("☯️ Popüler Tek-Çift Örüntüleri")
        parity_labels = ["-".join([s[0] for s in p]) for p in all_parities]
        st.bar_chart(pd.DataFrame(Counter(parity_labels).most_common(5), columns=['Örüntü', 'Adet']).set_index('Örüntü'))

    st.caption("Not: 18 ve 20 sayıları artık farklı onluk bloklarda (10-19 ve 20-29) değerlendirilmektedir.")
