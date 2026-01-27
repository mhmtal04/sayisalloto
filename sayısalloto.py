import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from itertools import combinations

# --- 1. Pozisyonel Baskı ve Zaman Ağırlığı Analizi ---

def analyze_advanced_stats(df):
    # Zaman Ağırlığı: Son çekilişler %50 daha etkili
    weights = np.linspace(0.5, 1.5, len(df))
    
    # Sayı Frekansları (Zaman Ağırlıklı)
    weighted_freq = Counter()
    for idx, row in enumerate(df.values):
        for num in row:
            weighted_freq[num] += weights[idx]
            
    # T1-T6 Pozisyon Baskısı (Hangi pozisyon hangi aralıkta sıkışmış?)
    pos_stats = {}
    for i, col in enumerate(df.columns):
        pos_stats[i+1] = {
            'min': int(df[col].quantile(0.05)),
            'max': int(df[col].quantile(0.95)),
            'avg': df[col].mean()
        }
    
    return weighted_freq, pos_stats

def predict_next_pattern(pattern_list):
    # Basit bir Markov zinciri mantığı: Son örüntüden sonra en çok ne gelmiş?
    # Şimdilik en popüler olanı ama bir sonrakine aday olanı seçer
    return Counter(pattern_list).most_common(1)[0][0]

# --- 2. Akıllı Kolon Üretim Motoru ---

def generate_strategic_column(target_pattern, hot, neutral, cold, pos_stats, pair_stats):
    sizes = list(map(int, target_pattern.split("-")))
    column = []
    
    # Onluk grupları belirle
    available_decades = list(range(9))
    random.shuffle(available_decades)
    selected_decades = available_decades[:len(sizes)]
    
    for i, size in enumerate(sizes):
        d = selected_decades[i]
        pool = [n for n in range(d * 10, d * 10 + 10) if 1 <= n <= 90]
        
        # Stratejik Seçim: Hem pozisyon baskısına uyan hem de karakteri (sıcak/soğuk) uygun olanlar
        picks = random.sample(pool, size) # Basit örnekleme, aşağıda puanla elenecek
        column.extend(picks)
    
    column = sorted(column[:6])
    return column

# --- 3. Çok Kriterli Puanlama Sistemi (Scoring) ---

def score_final_column(col, hot, cold, pair_stats, pos_stats, weighted_freq):
    score = 0
    # 1. Sıcak/Soğuk Dengesi
    for n in col:
        score += (weighted_freq.get(n, 0) * 0.1)
        if n in cold: score += 1.5 # "Kopabilecek" soğuk sayı bonusu
        
    # 2. Pozisyon Baskısı Uyumu (T1-T6 aralığında mı?)
    for i, n in enumerate(col):
        stats = pos_stats[i+1]
        if stats['min'] <= n <= stats['max']:
            score += 2.0
        else:
            score -= 1.0 # Pozisyon dışı sayı cezası
            
    # 3. Birlikte Çıkma (Pair) Gücü
    for pair in combinations(col, 2):
        score += pair_stats.get(pair, 0) * 0.5
        
    return round(score, 2)

# --- 4. Streamlit Arayüz Entegrasyonu ---

st.set_page_config(page_title="Loto Strateji Botu", layout="wide")
st.title("🎯 Stratejik Örüntü & Pozisyon Botu")

uploaded_file = st.file_uploader("Çekiliş geçmişini yükle (CSV)", type="csv")

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file).dropna()
    # (Burada veri temizleme adımları varsayılmıştır: S1-S6 seçimi)
    df = df_raw.iloc[:, -6:] # Son 6 kolonun sayı olduğunu varsayıyoruz
    
    # Analizleri Çalıştır
    weighted_freq, pos_stats = analyze_advanced_stats(df)
    pattern_counts, pattern_list = analyze_patterns(df) # Önceki koddaki fonk.
    pair_stats = pair_analysis(df) # Önceki koddaki fonk.
    
    # Tahmin Mekanizması
    next_p = predict_next_pattern(pattern_list)
    
    st.subheader("🔮 Bir Sonraki Çekiliş İçin Analiz")
    col1, col2, col3 = st.columns(3)
    col1.metric("Beklenen Örüntü", next_p)
    col2.metric("Sıcak Sayı Havuzu", len(weighted_freq))
    col3.metric("T1 İdeal Aralığı", f"{pos_stats[1]['min']}-{pos_stats[1]['max']}")

    # Kolon Üretimi
    candidates = []
    for _ in range(50): # 50 farklı kombinasyon dene, en iyisini seç
        c = generate_strategic_column(next_p, [], [], [], pos_stats, pair_stats)
        if len(c) == 6:
            s = score_final_column(c, [], [], pair_stats, pos_stats, weighted_freq)
            candidates.append((c, s))
    
    # En yüksek puanlıları göster
    top_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)[:5]
    
    st.divider()
    st.subheader("🚀 Analiz Edilen En Güçlü Kolonlar")
    for res_col, res_score in top_candidates:
        st.code(f"{res_col}  |  Stratejik Puan: {res_score}")

    fav = top_candidates[0]
    st.success(f"⭐ **FAVORİ SEÇİM:** {fav[0]} (Puan: {fav[1]})")
