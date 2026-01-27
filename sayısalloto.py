import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from itertools import combinations

# ------------------------
# Sayfa Ayarları
# ------------------------
st.set_page_config(
    page_title="🎯 Sayısal Loto Botu (Pattern Garantili)",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sayısal Loto Botu (Pattern Garantili)")
st.caption("Ondalık diziliş • Örüntü • Sıcak / Soğuk • Favori kolon")
st.divider()

# ------------------------
# Yardımcı Fonksiyonlar
# ------------------------
def decade(n):
    return (n-1)//10

def pattern_from_numbers(numbers):
    """Verilen sayılardan pattern çıkarır"""
    numbers = sorted(numbers)
    decades = [decade(n) for n in numbers]
    counts = []
    seen = set()
    for d in decades:
        if d not in seen:
            counts.append(decades.count(d))
            seen.add(d)
    return "-".join(map(str, counts))

def analyze_patterns(df):
    pattern_list = df.apply(lambda r: pattern_from_numbers(r.values), axis=1)
    return Counter(pattern_list), pattern_list.tolist()

def frequency_analysis(df):
    freq = Counter(df.values.flatten())
    avg = sum(freq.values())/len(freq)
    hot = [n for n,f in freq.items() if f>avg*1.3]
    cold = [n for n,f in freq.items() if f<avg*0.7]
    neutral = [n for n in range(1,91) if n not in hot and n not in cold]
    return hot, neutral, cold, freq

def pair_analysis(df):
    pair_counter = Counter()
    for row in df.values:
        for a,b in combinations(sorted(row),2):
            pair_counter[(a,b)] +=1
    return pair_counter

def generate_column_by_pattern(pattern, hot, neutral, cold, pair_stats, t_weights):
    """Pattern kurallarına göre kolon üretir"""
    group_sizes = list(map(int, pattern.split("-")))
    column = []
    used_numbers = set()

    for idx, size in enumerate(group_sizes):
        # Grup için ondalık seç (0–8)
        possible_decades = [d for d in range(9)]
        d = random.choice(possible_decades)

        # Ondalık içindeki sayılar
        pool = [n for n in range(d*10+1,d*10+11) if n not in used_numbers]

        # Pozisyon ağırlığı
        weighted_pool = []
        for n in pool:
            weight = t_weights[idx].get(n,1)
            weighted_pool.extend([n]*weight)

        # Tercih sırası: nötr -> sıcak -> cold
        preferred = [n for n in weighted_pool if n in neutral]
        if len(preferred)>=size:
            picks = random.sample(preferred,size)
        else:
            picks = random.sample(weighted_pool,size)

        column.extend(picks)
        used_numbers.update(picks)

    # Cold sayıyı rastgele ekleme
    if cold and random.random()<0.35:
        idx_replace = random.randint(0,len(column)-1)
        column[idx_replace] = random.choice(cold)

    return sorted(column)

def score_column(col, hot, cold, pair_stats):
    score = 0
    for n in col:
        if n in hot: score+=2
        if n in cold: score+=1
    for a,b in combinations(col,2):
        score+=pair_stats.get((a,b),0)*0.05
    return round(score,2)

def predict_next_pattern_by_history(pattern_list, window=2):
    sequences = defaultdict(Counter)
    for i in range(len(pattern_list)-window):
        key = tuple(pattern_list[i:i+window])
        next_pattern = pattern_list[i+window]
        sequences[key][next_pattern] +=1
    last_window = tuple(pattern_list[-window:])
    if last_window in sequences:
        return sequences[last_window].most_common(1)[0][0]
    return pattern_list[-1]

# ------------------------
# CSV Yükleme
# ------------------------
uploaded_file = st.file_uploader("📂 CSV yükle (T1–T6 veya S1–S6)", type="csv")
if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]
    s_cols = ["S1","S2","S3","S4","S5","S6"]
    t_cols = ["T1","T2","T3","T4","T5","T6"]
    if all(c in df_raw.columns for c in s_cols):
        df = df_raw[s_cols].copy()
    elif all(c in df_raw.columns for c in t_cols):
        df = df_raw[t_cols].copy()
    else:
        df = df_raw.iloc[:,1:7].copy()
    df = df.apply(pd.to_numeric, errors="coerce").dropna().astype(int)
    st.write(f"📄 {len(df)} çekiliş işlendi")

    # ------------------------
    # Pattern & İstatistik
    # ------------------------
    pattern_counts, pattern_list = analyze_patterns(df)
    hot, neutral, cold, freq = frequency_analysis(df)
    pair_stats = pair_analysis(df)

    # T1–T6 pozisyon baskısı
    t_weights=[]
    for i in range(6):
        col_freq = Counter(df.iloc[:,i])
        t_weights.append({n:freq for n,freq in col_freq.items()})

    # ------------------------
    # En çok çıkan 3 pattern
    # ------------------------
    st.subheader("🎯 Önerilen Kolonlar (En Çok Çıkan 3 Pattern)")
    results=[]
    for pattern,_ in pattern_counts.most_common(3):
        col = generate_column_by_pattern(pattern, hot, neutral, cold, pair_stats, t_weights)
        score = score_column(col, hot, cold, pair_stats)
        results.append((pattern,col,score))
        st.write(f"{pattern} → {col} | Puan: {score}")

    # ------------------------
    # Favori kolon (örüntüye göre)
    # ------------------------
    next_pattern = predict_next_pattern_by_history(pattern_list, window=2)
    fav_col = generate_column_by_pattern(next_pattern, hot, neutral, cold, pair_stats, t_weights)
    fav_score = score_column(fav_col, hot, cold, pair_stats)
    st.subheader("⭐ Favori Kolon (Örüntüye Dayalı Tahmin)")
    st.success(f"{fav_col} | Pattern: {next_pattern} | Puan: {fav_score}")

else:
    st.info("👆 Başlamak için CSV yükle") 
