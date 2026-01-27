import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from itertools import combinations

# -----------------------------
# Sayfa Ayarları
# -----------------------------
st.set_page_config(
    page_title="🎯 Sayısal Loto Örüntü & Diziliş Botu",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sayısal Loto Örüntü & Diziliş Botu")
st.caption("Ondalık diziliş • örüntü • sıcak/soğuk • favori kolon")
st.divider()

# -----------------------------
# Yardımcı Fonksiyonlar
# -----------------------------

def get_decade(n):
    return (n-1)//10  # 1-10 ->0, 11-20->1, ...

def detect_pattern(numbers):
    """Kolonun gerçek onluk (ondalık) pattern’ini çıkarır"""
    decades = [get_decade(n) for n in numbers]
    pattern = []
    i = 0
    while i < len(decades):
        count = 1
        while i+count < len(decades) and decades[i+count] == decades[i+count-1]:
            count += 1
        pattern.append(count)
        i += count
    return pattern

def pattern_to_str(pattern):
    return "-".join(map(str, pattern))

def analyze_patterns(df):
    pattern_counter = Counter()
    pattern_map = []
    for row in df.values:
        p = detect_pattern(list(row))
        s = pattern_to_str(p)
        pattern_counter[s] += 1
        pattern_map.append(s)
    return pattern_counter, pattern_map

def frequency_analysis(df):
    freq = Counter(df.values.flatten())
    avg = sum(freq.values()) / len(freq)
    hot = [n for n,f in freq.items() if f > avg*1.3]
    cold = [n for n,f in freq.items() if f < avg*0.7]
    neutral = [n for n in freq if n not in hot and n not in cold]
    return hot, neutral, cold, freq

def pair_analysis(df):
    counter = Counter()
    for row in df.values:
        for a,b in combinations(sorted(row),2):
            counter[(a,b)] +=1
    return counter

def generate_column_from_pattern(pattern, hot, neutral, cold, pair_stats):
    column = []
    used_decades = set()
    pattern_list = list(map(int, pattern.split("-")))

    for size in pattern_list:
        possible_decades = [d for d in range(0,9) if d not in used_decades]
        if not possible_decades: possible_decades = list(range(0,9))
        d = random.choice(possible_decades)
        used_decades.add(d)
        pool = [n for n in range(d*10+1,d*10+11) if n<=90]
        # Öncelik nötr sayılarda
        preferred = [n for n in pool if n in neutral]
        picks = random.sample(preferred, size) if len(preferred)>=size else random.sample(pool, size)
        column.extend(picks)

    # Rastgele soğuk sayılar ekle (35% ihtimal)
    if cold and random.random() <0.35:
        column[random.randint(0, len(column)-1)] = random.choice(cold)

    # Sıralama küçükten büyüğe
    return sorted(column)

def score_column(col, hot, cold, pair_stats):
    score = 0
    for n in col:
        if n in hot: score+=2
        if n in cold: score+=1
    for a,b in combinations(col,2):
        score += pair_stats.get((a,b),0)*0.05
    return round(score,2)

def predict_next_pattern(pattern_history):
    """Pattern geçmişine göre bir sonraki pattern tahmini"""
    transitions = defaultdict(Counter)
    for i in range(len(pattern_history)-1):
        transitions[pattern_history[i]][pattern_history[i+1]] +=1
    last = pattern_history[-1]
    if last in transitions:
        next_pattern = transitions[last].most_common(1)[0][0]
        return next_pattern
    else:
        # Eğer geçiş yoksa rastgele en çok çıkan pattern
        return Counter(pattern_history).most_common(1)[0][0]

# -----------------------------
# CSV Yükleme
# -----------------------------
uploaded_file = st.file_uploader("📂 CSV dosyasını yükle (T1–T6 veya S1–S6)", type="csv")

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]
    s_cols = ["S1","S2","S3","S4","S5","S6"]
    t_cols = ["T1","T2","T3","T4","T5","T6"]
    if all(c in df_raw.columns for c in t_cols):
        df = df_raw[t_cols].copy()
    elif all(c in df_raw.columns for c in s_cols):
        df = df_raw[s_cols].copy()
    else:
        df = df_raw.iloc[:,1:7].copy()
    df = df.apply(pd.to_numeric, errors="coerce").dropna().astype(int)
    st.success(f"✅ {len(df)} çekiliş başarıyla işlendi")
    st.divider()

    # -----------------------------
    # Pattern Analizi
    # -----------------------------
    st.subheader("📊 En Çok Çıkan Pattern’ler")
    pattern_counter, pattern_list = analyze_patterns(df)
    for p,c in pattern_counter.most_common(3):
        st.write(f"🔹 {p} → {c} kez")

    st.divider()
    st.subheader("🌡️ Sayı Davranışları")
    hot, neutral, cold, freq = frequency_analysis(df)
    c1,c2,c3 = st.columns(3)
    c1.metric("🔥 Sıcak", len(hot))
    c2.metric("⚖️ Nötr", len(neutral))
    c3.metric("❄️ Soğuk", len(cold))
    st.divider()

    st.subheader("🤝 Birlikte Çıkmayı Sevenler")
    pair_stats = pair_analysis(df)
    for pair, c in pair_stats.most_common(5):
        st.write(f"{pair} → {c} kez")
    st.divider()

    # -----------------------------
    # Kolon Üretimi
    # -----------------------------
    st.subheader("🎯 Önerilen Kolonlar (En Çok Çıkan 3 Pattern)")
    results=[]
    for p,_ in pattern_counter.most_common(3):
        col = generate_column_from_pattern(p, hot, neutral, cold, pair_stats)
        score = score_column(col, hot, cold, pair_stats)
        results.append((p,col,score))
        st.write(f"{p} dizilişi → {col} | Puan: {score}")

    # -----------------------------
    # Favori Kolon
    # -----------------------------
    fav_pattern = predict_next_pattern(pattern_list)
    fav_col = generate_column_from_pattern(fav_pattern, hot, neutral, cold, pair_stats)
    fav_score = score_column(fav_col, hot, cold, pair_stats)
    st.divider()
    st.subheader("⭐ FAVORİ KOLON (Tahmini Bir Sonraki Çekiliş Pattern’i)")
    st.success(f"{fav_col} | Pattern: {fav_pattern} | Puan: {fav_score}")

else:
    st.info("👆 Başlamak için CSV dosyasını yükle")
