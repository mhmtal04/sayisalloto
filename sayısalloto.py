import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from itertools import combinations

# -------------------------------------------------
# 1. TEMEL ANALİZ FONKSİYONLARI
# -------------------------------------------------

def get_decade(n: int) -> int:
    """Onluk (ondalık) diziliş grubu: 1-9->0, 10-19->1... 80-90->8"""
    if n == 90: return 8
    return n // 10

def generate_pattern(numbers):
    """Sayıların ondalık diziliş örüntüsünü çıkarır (Örn: 2-1-1-1-1)"""
    decades = [get_decade(n) for n in numbers]
    counts = Counter(decades)
    return "-".join(map(str, sorted(counts.values(), reverse=True)))

def analyze_patterns(df):
    """Tüm geçmişin diziliş örüntülerini analiz eder"""
    pattern_list = df.apply(lambda r: generate_pattern(r.values), axis=1)
    return Counter(pattern_list), pattern_list.tolist()

def frequency_analysis(df):
    """Sıcak, Soğuk ve Nötr sayıları belirler"""
    freq = Counter(df.values.flatten())
    avg = sum(freq.values()) / (len(freq) if len(freq) > 0 else 1)
    
    hot = [n for n, f in freq.items() if f > avg * 1.2]
    cold = [n for n, f in freq.items() if f < avg * 0.8]
    neutral = [n for n in freq if n not in hot and n not in cold]
    return hot, neutral, cold, freq

def pair_analysis(df):
    """Birlikte çıkmayı seven ikili sayıları analiz eder"""
    pair_counter = Counter()
    for row in df.values:
        for a, b in combinations(sorted(row), 2):
            pair_counter[(a, b)] += 1
    return pair_counter

# -------------------------------------------------
# 2. GELİŞMİŞ STRATEJİ FONKSİYONLARI (V2.0)
# -------------------------------------------------

def analyze_advanced_stats(df):
    """Zaman ağırlığı ve T1-T6 Pozisyon Baskısı analizi"""
    # Son çekilişler daha önemli (Zaman Ağırlığı)
    weights = np.linspace(0.5, 1.5, len(df))
    weighted_freq = Counter()
    for idx, row in enumerate(df.values):
        for num in row:
            weighted_freq[num] += weights[idx]
            
    # T1-T6 Pozisyon Baskısı (Hangi top hangi aralıkta çıkıyor?)
    pos_stats = {}
    for i, col in enumerate(df.columns):
        pos_stats[i+1] = {
            'min': int(df[col].quantile(0.10)),
            'max': int(df[col].quantile(0.90)),
            'avg': df[col].mean()
        }
    return weighted_freq, pos_stats

def predict_next_pattern(pattern_list):
    """Örüntü geçmişine bakarak bir sonraki muhtemel dizilişi tahmin eder"""
    if not pattern_list: return "1-1-1-1-1-1"
    # Son örüntüden sonra en sık gelen örüntüyü bul (Basit Markov)
    last_p = pattern_list[-1]
    next_candidates = []
    for i in range(len(pattern_list)-1):
        if pattern_list[i] == last_p:
            next_candidates.append(pattern_list[i+1])
    
    if next_candidates:
        return Counter(next_candidates).most_common(1)[0][0]
    return Counter(pattern_list).most_common(1)[0][0]

# -------------------------------------------------
# 3. ÜRETİM VE PUANLAMA MOTORU
# -------------------------------------------------

def generate_strategic_column(target_pattern, hot, neutral, cold, pos_stats):
    """Belirlenen örüntüye ve onluk kurallara göre kolon üretir"""
    try:
        sizes = list(map(int, target_pattern.split("-")))
    except:
        sizes = [1,1,1,1,1,1]
        
    column = []
    available_decades = list(range(9))
    random.shuffle(available_decades)
    
    for size in sizes:
        if not available_decades: break
        d = available_decades.pop()
        pool = [n for n in range(d * 10, d * 10 + 10) if 1 <= n <= 90]
        if len(pool) < size: continue
        picks = random.sample(pool, size)
        column.extend(picks)
        
    return sorted(column[:6])

def score_final_column(col, hot, cold, pair_stats, pos_stats, weighted_freq):
    """11 Kriterli Puanlama Sistemi"""
    score = 0
    # 1. Pozisyon Baskısı (T1-T6 aralık uyumu)
    for i, n in enumerate(col):
        stats = pos_stats.get(i+1, {'min': 1, 'max': 90})
        if stats['min'] <= n <= stats['max']:
            score += 3.0 # Pozisyon uyumu çok önemli
        
    # 2. Sıcak/Soğuk/Nötr Dengesi
    for n in col:
        score += (weighted_freq.get(n, 0) * 0.1)
        if n in hot: score += 1.0
        if n in cold: score += 2.0 # "Kopabilecek" soğuk sayıya yüksek puan
        
    # 3. İkili Kombinasyon (Birlikte çıkma)
    for pair in combinations(col, 2):
        score += pair_stats.get(pair, 0) * 0.4
        
    return round(score, 2)

# -------------------------------------------------
# 4. STREAMLIT ARAYÜZÜ
# -------------------------------------------------

st.set_page_config(page_title="Loto Strateji Botu v2", layout="wide")
st.title("🎯 Sayısal Loto Stratejik Analiz Botu")
st.caption("Onluk Diziliş • Pozisyon Baskısı • Zaman Ağırlığı • Puanlama")

uploaded_file = st.file_uploader("📂 CSV Dosyasını Yükle (T1-T6 veya S1-S6)", type="csv")

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]
    
    # Kolon seçimi
    s_cols = ["S1", "S2", "S3", "S4", "S5", "S6"]
    t_cols = ["T1", "T2", "T3", "T4", "T5", "T6"]
    
    if all(c in df_raw.columns for c in s_cols):
        df = df_raw[s_cols].copy()
    elif all(c in df_raw.columns for c in t_cols):
        df = df_raw[t_cols].copy()
    else:
        df = df_raw.iloc[:, 1:7].copy()

    df = df.apply(pd.to_numeric, errors="coerce").dropna().astype(int)
    
    # --- Analizleri Çalıştır ---
    weighted_freq, pos_stats = analyze_advanced_stats(df)
    pattern_counts, pattern_list = analyze_patterns(df)
    pair_stats = pair_analysis(df)
    hot, neutral, cold, raw_freq = frequency_analysis(df)
    next_p = predict_next_pattern(pattern_list)
    
    # --- Gösterge Paneli ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tahmin Edilen Örüntü", next_p)
    c2.metric("Sıcak Sayılar", len(hot))
    c3.metric("Soğuk Sayılar", len(cold))
    c4.metric("Analiz Edilen Çekiliş", len(df))
    
    st.divider()

    # --- Kolon Üretimi ve Süzme ---
    st.subheader("🚀 Stratejik Olarak Üretilen Kolonlar")
    
    candidates = []
    # 1000 simülasyon yap ve en iyi puan alanları seç
    for _ in range(1000):
        # Tahmin edilen örüntüye göre üret
        c = generate_strategic_column(next_p, hot, neutral, cold, pos_stats)
        if len(c) == 6:
            s = score_final_column(c, hot, cold, pair_stats, pos_stats, weighted_freq)
            candidates.append((c, s))
            
    # En yüksek puanlı 5 taneyi al
    top_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)[:5]

    for i, (col, score) in enumerate(top_candidates):
        actual_p = generate_pattern(col)
        st.write(f"{i+1}. Öneri: `{col}` | Örüntü: **{actual_p}** | Stratejik Puan: **{score}**")

    # --- Favori Kolon ---
    st.divider()
    fav_col, fav_score = top_candidates[0]
    st.subheader("⭐ GÜNÜN FAVORİ KOLONU")
    st.success(f"Sayılar: {fav_col}  |  Toplam Puan: {fav_score}  |  Hedef Diziliş: {next_p}")
    
    with st.expander("Pozisyon Baskısı (T1-T6) Detayları"):
        st.write("Her pozisyonun (topun) tarihsel olarak çıkması beklenen sayı aralıkları:")
        st.json(pos_stats)
else:
    st.info("Lütfen geçmiş çekilişleri içeren CSV dosyasını yükleyin.")
