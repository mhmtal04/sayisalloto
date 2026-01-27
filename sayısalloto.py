import streamlit as st
import pandas as pd
import random
from collections import Counter, defaultdict
from itertools import combinations

# -------------------------------------------------
# Sayfa Ayarları
# -------------------------------------------------
st.set_page_config(
    page_title="🎯 Sayısal Loto Örüntü & Diziliş Botu",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Sayısal Loto Örüntü & Diziliş Botu")
st.caption("Ondalık diziliş • örüntü • sıcak / soğuk • favori kolon")
st.divider()

# -------------------------------------------------
# Yardımcı Fonksiyonlar
# -------------------------------------------------

def decade(n: int) -> int:
    """Sayının ondalığını döndürür (1-10 → 0, 11-20 → 1, ...)"""
    return (n-1)//10

def generate_pattern(numbers):
    """
    Sayılar küçükten büyüğe sıralanmış olmalı.
    Aynı ondalıkta olan sayıları gruplar ve pattern oluşturur.
    """
    numbers = sorted(numbers)
    decades = [decade(n) for n in numbers]
    pattern = []
    i = 0
    while i < len(decades):
        count = 1
        for j in range(i+1, len(decades)):
            if decades[j] == decades[i]:
                count += 1
            else:
                break
        pattern.append(count)
        i += count
    return "-".join(map(str, pattern))

def analyze_patterns(df):
    """Tüm veriler için pattern çıkar ve say"""
    pattern_list = df.apply(lambda r: generate_pattern(r.values), axis=1)
    return Counter(pattern_list), pattern_list.tolist()

def frequency_analysis(df):
    """Sıcak / nötr / soğuk sayılar"""
    freq = Counter(df.values.flatten())
    avg = sum(freq.values()) / len(freq)
    hot = [n for n, f in freq.items() if f > avg*1.3]
    cold = [n for n, f in freq.items() if f < avg*0.7]
    neutral = [n for n in freq if n not in hot and n not in cold]
    return hot, neutral, cold, freq

def pair_analysis(df):
    """Birlikte çıkmayı seven sayılar"""
    pair_counter = Counter()
    for row in df.values:
        for a,b in combinations(sorted(row),2):
            pair_counter[(a,b)] += 1
    return pair_counter

def generate_column_by_pattern(pattern, hot, neutral, cold):
    """
    Pattern’e uygun kolon üretir:
    - Onluk grupları kontrol edilir
    - Tekrar yok
    - Küçükten büyüğe sıralı
    """
    group_sizes = list(map(int, pattern.split("-")))
    used_numbers = set()
    column = []
    available_decades = list(range(9))
    random.shuffle(available_decades)
    
    for size in group_sizes:
        # Uygun ondalık seç
        decade_selected = None
        for d in available_decades:
            pool = [n for n in range(d*10+1, d*10+11) if n not in used_numbers]
            if len(pool) >= size:
                decade_selected = d
                break
        if decade_selected is None:
            decade_selected = random.choice(available_decades)
            pool = [n for n in range(decade_selected*10+1, decade_selected*10+11) if n not in used_numbers]
        
        picks = random.sample(pool, size)
        column.extend(picks)
        used_numbers.update(picks)
        available_decades.remove(decade_selected)
    
    column.sort()
    return column

def score_column(col, hot, cold, pair_stats):
    score = 0
    for n in col:
        if n in hot: score += 2
        if n in cold: score += 1
    for a,b in combinations(col,2):
        score += pair_stats.get((a,b),0)*0.05
    return round(score,2)

def predict_next_pattern(pattern_list):
    """
    Basit örüntü tahmini: son pattern sonrası en çok gelen patterni döndürür
    """
    transitions = defaultdict(Counter)
    for i in range(len(pattern_list)-1):
        transitions[pattern_list[i]][pattern_list[i+1]] += 1
    last_pattern = pattern_list[-1]
    if last_pattern in transitions:
        return transitions[last_pattern].most_common(1)[0][0]
    else:
        # Görülmemiş pattern → rastgele en çok çıkan pattern
        return None

# -------------------------------------------------
# CSV Yükleme
# -------------------------------------------------
uploaded_file = st.file_uploader("📂 CSV dosyasını yükle (T1–T6 veya S1–S6)", type="csv")

if uploaded_file:
    st.subheader("📥 Veri Okuma & Temizleme")
    df_raw = pd.read_csv(uploaded_file)
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]

    s_cols = ["S1","S2","S3","S4","S5","S6"]
    t_cols = ["T1","T2","T3","T4","T5","T6"]

    if all(c in df_raw.columns for c in s_cols):
        df = df_raw[s_cols].copy()
        st.write("✅ S1–S6 kolonları kullanıldı")
    elif all(c in df_raw.columns for c in t_cols):
        df = df_raw[t_cols].copy()
        st.write("✅ T1–T6 kolonları kullanıldı")
    else:
        df = df_raw.iloc[:,1:7].copy()
        st.write("⚠️ Kolon isimleri bulunamadı → 2–7. kolonlar alındı")

    df = df.apply(pd.to_numeric, errors="coerce").dropna().astype(int)
    st.write(f"✅ {len(df)} çekiliş başarıyla işlendi")
    st.divider()

    # -------------------------------------------------
    # Analizler
    # -------------------------------------------------
    st.subheader("📊 En Çok Çıkan Dizilişler")
    pattern_counts, pattern_list = analyze_patterns(df)
    for p,c in pattern_counts.most_common(3):
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
    for pair,c in pair_stats.most_common(5):
        st.write(f"{pair} → {c} kez")
    st.divider()

    # -------------------------------------------------
    # Kolon Üretimi
    # -------------------------------------------------
    st.subheader("🎯 Önerilen Kolonlar (En Çok Çıkan 3 Pattern)")
    results = []
    for pattern,_ in pattern_counts.most_common(3):
        col = generate_column_by_pattern(pattern, hot, neutral, cold)
        score = score_column(col, hot, cold, pair_stats)
        results.append((pattern,col,score))
        st.write(f"{pattern} dizilişi → {col} | Puan: {score}")

    # Favori Kolon (örüntü tahmini)
    next_pattern = predict_next_pattern(pattern_list)
    if next_pattern is None:
        next_pattern = results[0][0]  # Görülmemiş pattern → en çok çıkan pattern
    fav_col = generate_column_by_pattern(next_pattern, hot, neutral, cold)
    fav_score = score_column(fav_col, hot, cold, pair_stats)
    st.divider()
    st.subheader("⭐ FAVORİ KOLON (Örüntüye Dayalı Tahmin)")
    st.success(f"{fav_col} | Pattern: {next_pattern} | Puan: {fav_score}")

else:
    st.info("👆 Başlamak için CSV dosyasını yükle")
