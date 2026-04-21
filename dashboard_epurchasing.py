import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard E-Purchasing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
# Membuat tampilan margin dan padding rapi, ala Looker Studio
st.markdown("""
    <style>
    .main {
        background-color: #f7f9fc;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1e3d59;
    }
    .stDataFrame {
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stMetricValue"] {
        color: #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("📊 Dashboard Analisis E-Purchasing")
# st.markdown("- **Tujuan**: Visualisasi Data Pengadaan/Purchasing mirip dengan Looker Studio.")

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    file_path = 'data E-Purchasing (2).xlsx'
    # Membaca data dengan nama sheet yang benar ('Data Total.' dengan titik di belakang)
    df = pd.read_excel(file_path, sheet_name='Data Total.')
    
    # Membersihkan nama kolom (menghilangkan spasi ekstra di akhir)
    df.columns = df.columns.str.strip()
    
    # Memastikan format numerik
    df['pagu'] = pd.to_numeric(df['pagu'], errors='coerce').fillna(0)
    df['Total Realisasi'] = pd.to_numeric(df['Total Realisasi'], errors='coerce').fillna(0)
    
    return df

# Menangkap error jika file tidak ada atau formatnya berubah
try:
    with st.spinner("Load Data in Progress..."):
        df = load_data()
except Exception as e:
    st.error(f"⚠️ Gagal memuat data dari file Excel. Pastikan file 'data E-Purchasing (2).xlsx' berada di folder yang sama. Error detail: {e}")
    st.stop()

def format_rupiah(x):
    if x >= 1e12: return f"Rp {x/1e12:.2f} T"
    elif x >= 1e9: return f"Rp {x/1e9:.2f} M"
    elif x >= 1e6: return f"Rp {x/1e6:.2f} Jt"
    else: return f"Rp {x:,.0f}"

# --- SIDEBAR (FILTER) ---
st.sidebar.header("🎛️ Filter Panel")
satker_list = ["Semua Satker"] + sorted(df['nama_satker'].dropna().unique().tolist())
selected_satker = st.sidebar.selectbox("Filter berdasarkan Satuan Kerja:", satker_list)

# Proses filter data
if selected_satker != "Semua Satker":
    df_filtered = df[df['nama_satker'] == selected_satker]
else:
    df_filtered = df

# Metric Scorecards (Highlight atas)
st.markdown("---")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Total Pagu (Anggaran)", value=f"Rp {df_filtered['pagu'].sum():,.0f}")
kpi2.metric(label="Total Realisasi", value=f"Rp {df_filtered['Total Realisasi'].sum():,.0f}")
serapan_persen = (df_filtered['Total Realisasi'].sum() / df_filtered['pagu'].sum() * 100) if df_filtered['pagu'].sum() > 0 else 0
kpi3.metric(label="Persentase Serapan", value=f"{serapan_persen:.2f} %")
st.markdown("---")

# --- ROW 1: Chart 1 & Chart 2 ---
col1, col2 = st.columns(2)

# 1. Perbandingan Pagu vs Realisasi
with col1:
    st.subheader("1. Pagu vs Realisasi")
    st.markdown("Membandingkan jumlah pagu/anggaran dengan total nilai realisasi.")
    
    if selected_satker == "Semua Satker":
        # Jika semua satker, tunjukkan bar bertingkat (Top 10 satker secara default)
        df_vs = df_filtered.groupby('nama_satker')[['pagu', 'Total Realisasi']].sum().nlargest(10, 'pagu').reset_index()
        fig1 = go.Figure(data=[
            go.Bar(name='Pagu', x=df_vs['nama_satker'], y=df_vs['pagu'], marker_color='#93c47d'),
            go.Bar(name='Realisasi', x=df_vs['nama_satker'], y=df_vs['Total Realisasi'], marker_color='#38761d')
        ])
        fig1.update_layout(
            barmode='group', 
            xaxis_title="Top 10 Satker", 
            yaxis_title="Nilai (Rp)",
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        # Jika satu satker dipilih, buat chart bar satuan
        total_pagu = df_filtered['pagu'].sum()
        total_real = df_filtered['Total Realisasi'].sum()
        fig1 = go.Figure(data=[
            go.Bar(name='Pagu', x=['Total Anggaran'], y=[total_pagu], marker_color='#93c47d', width=0.4),
            go.Bar(name='Realisasi', x=['Total Realisasi'], y=[total_real], marker_color='#38761d', width=0.4)
        ])
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)

# 2. Top 5 Satker Berdasarkan Pagu
with col2:
    st.subheader("2. Top 5 Satker (Pagu Tertinggi)")
    if selected_satker == "Semua Satker":
        st.markdown("5 Satuan Kerja dengan alokasi anggaran terbesar.")
        top5_satker = df_filtered.groupby('nama_satker')['pagu'].sum().nlargest(5).sort_values(ascending=True).reset_index()
        top5_satker['pagu_formatted'] = top5_satker['pagu'].apply(format_rupiah)
        
        # Horizontal Bar Chart
        fig2 = px.bar(top5_satker, x='pagu', y='nama_satker', orientation='h',
                      text='pagu_formatted', color_discrete_sequence=['#5b9bd5'])
        fig2.update_traces(textfont_size=12, textangle=0, textposition="outside")
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Alokasi Pagu (Rp)", 
            yaxis_title="(Berdasarkan Terbesar)",
            margin=dict(l=20, r=20, t=30, b=40)
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info(f"Opsi Top 5 tidak relevan karena Anda sedang memfilter 1 Satker spesifik ({selected_satker}).")

# --- KOMPOSISI IDENTIFIKASI ---
st.markdown("---")
st.subheader("3. Komposisi Identifikasi Pembelian")

if 'Identifikasi' in df_filtered.columns:
    st.markdown("Proporsi serapan divisualisasikan dengan **Treemap** (kotak besar = nilai serapan tinggi) agar mudah memuat banyak tipe identifikasi.")
    
    if selected_satker == "Semua Satker":
        # Siapkan filter untuk Top 10 Satker
        top10_satker_name = df_filtered.groupby('nama_satker')['Total Realisasi'].sum().nlargest(10).index
        df_komposisi = df_filtered[df_filtered['nama_satker'].isin(top10_satker_name)]
        df_komposisi = df_komposisi.groupby(['nama_satker', 'Identifikasi'])['Total Realisasi'].sum().reset_index()
        # Hanya ambil yang lebih dari 0 agar treemap valid
        df_komposisi = df_komposisi[df_komposisi['Total Realisasi'] > 0]
        
        # Gunakan Treemap sebagai solusi elegan untuk banyaknya ragam Identifikasi
        fig3 = px.treemap(
            df_komposisi, 
            path=[px.Constant("Top 10 Satker"), 'nama_satker', 'Identifikasi'], 
            values='Total Realisasi',
            color='Total Realisasi',
            color_continuous_scale=px.colors.sequential.Teal
        )
        fig3.update_traces(root_color="lightgrey", textinfo="label+percent parent")
        fig3.update_layout(margin=dict(t=10, l=10, r=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)
        
    else:
        # Jika 1 Satker dipilih, Treemap nya fokus pada Identifikasi milik Satker tsb
        df_komposisi = df_filtered.groupby('Identifikasi')['Total Realisasi'].sum().reset_index()
        df_komposisi = df_komposisi[df_komposisi['Total Realisasi'] > 0]
        
        # Jika datanya kosong (tidak ada yang nilainya > 0)
        if df_komposisi.empty:
            st.info("Seluruh nilai total realisasi pada satker ini adalah 0, grafik tidak dapat digambar.")
        else:
            fig3 = px.treemap(
                df_komposisi,
                path=[px.Constant(selected_satker), 'Identifikasi'],
                values='Total Realisasi',
                color='Total Realisasi',
                color_continuous_scale=px.colors.sequential.Teal
            )
            fig3.update_traces(root_color="lightgrey", textinfo="label+percent root")
            fig3.update_layout(margin=dict(t=10, l=10, r=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Kolom 'Identifikasi' tidak tersedia dalam data.")

# --- PEMBELIAN BERULANG ---
st.markdown("---")
st.subheader("4. Analisis Pembelian Berulang")
st.markdown("Daftar Identifikasi/Item yang dibeli **lebih dari 1 kali**.")

# Kontrol khusus untuk memilih satker di panel Analisis Pembelian Berulang
satker_lists_rep = list(df['nama_satker'].dropna().unique())
selected_satker_rep = st.selectbox(
    "Pilih Satker Khusus Tabel Ini:", 
    ["Semua Satker (Ikut Filter Utama)"] + sorted(satker_lists_rep)
)

if selected_satker_rep != "Semua Satker (Ikut Filter Utama)":
    df_rep_target = df[df['nama_satker'] == selected_satker_rep]
else:
    df_rep_target = df_filtered

# Kolom utama untuk deteksi item repetitive
ident_col = 'Identifikasi' if 'Identifikasi' in df_rep_target.columns else 'nama_paket'

# Menghitung Frekuensi Pembelian
df_rep = df_rep_target.groupby(['nama_satker', ident_col]).size().reset_index(name='Frekuensi Transaksi')
df_rep_nilai = df_rep_target.groupby(['nama_satker', ident_col])['Total Realisasi'].sum().reset_index()

# Gabung data frekuensi & nilai
df_rep_final = pd.merge(df_rep, df_rep_nilai, on=['nama_satker', ident_col])

# FILTER: Hanya tampilkan yang dibeli LEBIH DARI 1 KALI
df_rep_final = df_rep_final[df_rep_final['Frekuensi Transaksi'] > 1]
df_rep_final = df_rep_final.sort_values(by='Frekuensi Transaksi', ascending=False)

if not df_rep_final.empty:
    # Terapkan format Nominal Uang dengan cara menukar koma (ribuan dari Python) menjadi titik gaya Indonesia
    # Contoh: Rp 1,500,000 -> Rp 1.500.000
    df_rep_final['Total Nilai (Rp)'] = df_rep_final['Total Realisasi'].apply(
        lambda x: f"Rp {x:,.0f}".replace(",", ".")
    )
    
    # Tampilkan DataFrame dengan opsi custom styling pada Streamlit
    st.dataframe(
        df_rep_final[['nama_satker', ident_col, 'Frekuensi Transaksi', 'Total Nilai (Rp)']],
        use_container_width=True,
        column_config={
            'Frekuensi Transaksi': st.column_config.ProgressColumn(
                "Frekuensi", help="Total pengulangan pembelian",
                format="%f", min_value=0, max_value=int(df_rep_final['Frekuensi Transaksi'].max())
            ),
            'Total Nilai (Rp)': st.column_config.TextColumn(
                "Total Realisasi"
            )
        },
        height=400,
        hide_index=True
    )
else:
    st.info("💡 Tidak ditemukan transaksi/pembelian yang dilakukan secara berulang (> 1 kali) pada filter ini.")
