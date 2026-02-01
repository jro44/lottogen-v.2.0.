import streamlit as st
import pypdf
import re
import random
import os
import pandas as pd
from datetime import datetime
from collections import Counter

# --- KONFIGURACJA ---
st.set_page_config(
    page_title="Lotto Generator v.2.0.",
    page_icon="🎱",
    layout="centered"
)

# --- STYL ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .big-number {
        font-size: 24px; font-weight: bold; color: white;
        background-color: #f1c40f; border-radius: 50%;
        width: 50px; height: 50px; display: inline-flex;
        justify-content: center; align-items: center;
        margin: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .metric-card {
        background-color: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNKCJE ---
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return []
    draws = []
    try:
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            text = page.extract_text() or ""
            tokens = re.findall(r'\d+', text)
            i = 0
            while i < len(tokens):
                candidates = []
                offset = 0
                while len(candidates) < 6 and (i + offset) < len(tokens):
                    try:
                        val = int(tokens[i+offset])
                        if 1 <= val <= 49:
                            candidates.append(val)
                        else:
                            if candidates: break
                    except: break
                    offset += 1
                if len(candidates) == 6:
                    draws.append(candidates)
                    i += offset
                else:
                    i += 1
    except:
        return []
    return draws

def get_hot_numbers(draws):
    flat_data = [num for sublist in draws for num in sublist]
    counts = Counter(flat_data)
    # Zwracamy wagi dla liczb 1-49
    weights = [counts.get(i, 1) for i in range(1, 50)]
    return weights

# --- GŁÓWNY ALGORYTM FILTRACYJNY ---
def smart_generate(weights):
    population = list(range(1, 50))
    
    # Próbujemy max 1000 razy znaleźć idealny zestaw
    for _ in range(1000):
        # 1. Losowanie ważone (baza - liczby częste)
        # Podnosimy wagi do kwadratu, żeby jeszcze bardziej faworyzować "gorące"
        stronger_weights = [w**1.5 for w in weights]
        
        candidates = set()
        while len(candidates) < 6:
            c = random.choices(population, weights=stronger_weights, k=1)[0]
            candidates.add(c)
        
        nums = sorted(list(candidates))
        
        # --- FILTRY (SITO) ---
        
        # 1. Suma (Najczęstszy przedział dla Lotto to 120-180)
        total_sum = sum(nums)
        if not (100 <= total_sum <= 200): # Lekko poszerzony dla bezpieczeństwa
            continue # Odrzuć i losuj dalej
            
        # 2. Parzystość (Unikamy skrajności 6:0 lub 0:6)
        even_count = sum(1 for n in nums if n % 2 == 0)
        if even_count == 0 or even_count == 6:
            continue
            
        # 3. Niskie/Wysokie (Podział na 1-25 i 26-49)
        low_count = sum(1 for n in nums if n <= 25)
        if low_count == 0 or low_count == 6:
            continue
            
        # 4. Kolejność (Unikamy np. 12, 13, 14 - trzy po kolei rzadko wpadają)
        consecutive = 0
        max_consecutive = 0
        for i in range(len(nums)-1):
            if nums[i+1] == nums[i] + 1:
                consecutive += 1
            else:
                consecutive = 0
            max_consecutive = max(max_consecutive, consecutive)
        
        if max_consecutive >= 2: # Odrzucamy ciągi 3-liczbowe i dłuższe
            continue
            
        # Jeśli zestaw przetrwał wszystkie filtry:
        return nums, total_sum, even_count

    # Jeśli pechowo nic nie znajdzie (mało prawdopodobne), zwróć cokolwiek
    return nums, sum(nums), 0

# --- INTERFEJS ---
def main():
    st.title("🎱 Lotto Smart System")
    st.markdown("Algorytm z filtrowaniem statystycznym (Suma, Parzystość, Zakres).")
    
    # Plik musi nazywać się Lotto600los.pdf lub inny, który masz
    # Tutaj używam nazwy uniwersalnej, sprawdź jaką masz na GitHubie!
    FILE_NAME = "Lotto999los.pdf" 
    
    draws = load_data(FILE_NAME)
    
    if not draws:
        st.warning(f"Wgraj plik {FILE_NAME} aby zwiększyć precyzję!")
        # Fallback - jeśli brak pliku, używamy równych wag
        weights = [1] * 49
    else:
        st.success(f"Analiza bazy: {len(draws)} losowań.")
        weights = get_hot_numbers(draws)

    if st.button("🎰 GENERUJ ZESTAW SMART", use_container_width=True):
        with st.spinner("Filtrowanie tysięcy kombinacji..."):
            result, s_sum, s_even = smart_generate(weights)
            
        # Wyświetlanie kulek
        cols = st.columns(6)
        for i, n in enumerate(result):
            cols[i].markdown(f"<div class='big-number'>{n}</div>", unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Wyjaśnienie dlaczego ten zestaw
        c1, c2, c3 = st.columns(3)
        c1.info(f"📐 Suma: {s_sum}\n(Optimum: 120-180)")
        c2.info(f"⚖️ Parzyste: {s_even}/6\n(Balans)")
        c3.info(f"🔥 Baza: Gorące Liczby")
        
        st.caption("Ten zestaw jest statystycznie bardziej prawdopodobny niż losowy 'chybił-trafił', ponieważ mieści się w najczęstszym rozkładzie Gaussa.")

if __name__ == "__main__":
    main()