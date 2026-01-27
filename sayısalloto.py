import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from itertools import combinations

# -------------------- Sayfa Ayarları --------------------
st.set_page_config(
    page_title="🎯 Sayısal Loto Örüntü & Diziliş Botu",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sayısal Loto Örüntü & Diziliş Botu")
st.caption("Ondalık diziliş • örüntü (geçiş) • sıcak / soğuk • favori kolon")
st.divider()

# -------------------- Yardımcı Fonksiyonlar --------------------

def decade(n: int) -> int:
    """Bir sayının onluk (ondalık) değerini döndürür"""
    return (n-1)//10  # 1-10 -> 0, 11-20 ->1, ... 81-90 -> 8

def generate_pattern(numbers):
    """Verilen 6 sayıyı pattern koduna çevirir (ondalık gruplarına göre)"""
    decades = [decade(n) for n in numbers]
    counts = Counter()
    i = 0
    while i < len(decades):
        d = decades[i]
        cnt = 1
        for j in range(i+1, len(decades)):
            if decades[j] == d:
                cnt +=1
            else:
                break
        counts[cnt] +=1
        i += cnt
    # pattern dizisi: sayıları küçükten büyüğe diz, grup sayıları sırayla
    # ör: 1-2-1-1-1
    pattern_list = []
    i=0
    while i < len(decades):
        d = decades[i]
        cnt = 1
        for j in range(i+1, len(decades)):
            if decades[j]==d:
                cnt+=1
            else:
                break
        pattern_list.append(cnt)
        i+=cnt
    return "-".join(map(str, pattern_list))

def analyze_patterns(df):
    """Tüm çekilişleri analiz eder, pattern listesi ve sayım döndürür"""
    pattern_list = [generate_pattern(list(row)) for row in df.values]
    pattern_counter = Counter(pattern_list)
    return pattern_counter, pattern_list

def frequency_analysis(df):
    """Sıcak, nötr, soğuk sayıları döndürür"""
    all_nums = df.values.flatten()
    freq = Counter(all_nums)
    avg = sum(freq.values()) / len(freq)
    hot = [n for n,f in freq.items() if f>avg*1.3]
    cold = [n for n,f in freq.items() if f<avg*0.7]
    neutral = [n for n in freq if n not in hot and n not in cold]
    return hot, neutral, cold, freq

def pair_analysis(df):
    """Birlikte çıkmayı seven sayıları analiz eder"""
    counter = Counter()
    for row in df.values:
        for a,b in combinations(sorted(row),2):
            counter[(a,b)] +=1
    return counter

def generate_column(pattern, hot, neutral, cold, pair_stats, last_pattern=None):
    """Pattern’e uygun kolon üretir"""
    column = []
    used_decades = set()
    pattern_sizes = list(map(int, pattern.split("-")))

    for idx, size in enumerate(pattern_sizes):
        # Kullanılacak ondalık grupları
        possible_decades = [d for d in range(0,9) if d not in used_decades]
        if size>1:
            # Eğer aynı ondalıkta birden fazla sayı olacak
            d = random.choice(possible_decades)
            used_decades.add(d)
        else:
            d = random.choice(possible_decades)
            used_decades.add(d)

        # Havuz: ondalık grubu içindeki sayılar
        pool = [n for n in range(d*10+1,d*10+11) if n<=90]

        # Tercih edilen sayılar: sıcak, nötr ve soğuk
        preferred = [n for n in pool if n in neutral or n in hot or n in cold]
        if len(preferred)>=size:
            picks = random.sample(preferred,size)
        else:
            picks = random.sample(pool,size)

        # Aynı ondalıkta olacaksa ve birden fazla sayı gerekiyorsa
        if size>1:
            while len(picks)<size:
                picks.append(random.choice(pool))
        column.extend(picks)

    # Kolonu küçükten büyüğe sırala
    column = sorted(column)
    return column[:6]

def score_column(col, hot, cold, pair_stats):
    """Kolon puanlama"""
    score=0
    for n in col:
        if n in hot:
            score+=2
        if n in cold:
            score+=1
    for a,b in combinations(col,2):
        score += pair_stats.get((a,b),0)*0.05
    return round(score,2)

# -------------------- CSV Yükleme --------------------

uploaded_file = st.file_uploader(
    "📂 CSV dosyasını yükle (T1–T6 veya S1–S6)",
    type="csv"
)

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]
    t_cols = ["T1","T2","T3","T4","T5","T6"]
    s_cols = ["S1","S2","S3","S4","S5","S6"]
    if all(c in df_raw.columns for c in t_cols):
        df = df_raw[t_cols].copy()
    elif all(c in df_raw.columns for c in s_cols):
        df = df_raw[s_cols].copy()
    else:
        df = df_raw.iloc[:,1:7].copy()
    df = df.apply(pd.to_numeric, errors="coerce").dropna().astype(int)
    st.write(f"✅ {len(df)} çekiliş başarıyla işlendi")

    # -------------------- Analiz --------------------
    st.subheader("📊 En Çok Çıkan Dizilişler")
    pattern_counts, pattern_list = analyze_patterns(df)
    for p,c in pattern_counts.most_common(3):
        st.write(f"🔹 {p} → {c} kez")

    st.subheader("🌡️ Sayı Davranışları")
    hot, neutral, cold, _ = frequency_analysis(df)
    st.write(f"🔥 Sıcak: {len(hot)} | ⚖️ Nötr: {len(neutral)} | ❄️ Soğuk: {len(cold)}")

    st.subheader("🤝 Birlikte Çıkmayı Sevenler")
    pair_stats = pair_analysis(df)
    for pair,c in pair_stats.most_common(5):
        st.write(f"{pair} → {c} kez")

    # -------------------- Kolon Üretimi --------------------
    st.subheader("🎯 Önerilen Kolonlar (En Çok Çıkan 3 Pattern)")
    results=[]
    for pattern,_ in pattern_counts.most_common(3):
        col = generate_column(pattern, hot, neutral, cold, pair_stats)
        score = score_column(col, hot, cold, pair_stats)
        results.append((pattern,col,score))
        st.write(f"{pattern} → {col} | Puan: {score}")

    # -------------------- Favori Kolon --------------------
    st.subheader("⭐ FAVORİ KOLON (Örüntüye Dayalı Tahmin)")
    last_pattern = pattern_list[-1]
    # Tahmini bir sonraki pattern
    # Basit örüntü: son pattern’e göre aynı pattern
    next_pattern = last_pattern
    fav_col = generate_column(next_pattern, hot, neutral, cold, pair_stats, last_pattern)
    fav_score = score_column(fav_col, hot, cold, pair_stats)
    st.success(f"{fav_col} | Pattern: {next_pattern} | Puan: {fav_score}")

else:
    st.info("👆 Başlamak için CSV dosyasını yükle")
