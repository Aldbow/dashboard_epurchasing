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

# Filter Tahun
if 'tahun_anggaran' in df.columns:
    tahun_list = ["Semua Tahun"] + sorted(df['tahun_anggaran'].dropna().unique().tolist(), reverse=True)
    selected_tahun = st.sidebar.selectbox("Filter berdasarkan Tahun:", tahun_list)
else:
    selected_tahun = "Semua Tahun"

# Filter Satker
satker_list = ["Semua Satker"] + sorted(df['nama_satker'].dropna().unique().tolist())
selected_satker = st.sidebar.selectbox("Filter berdasarkan Satuan Kerja:", satker_list)

# Proses filter data
df_filtered = df.copy()

if selected_tahun != "Semua Tahun":
    df_filtered = df_filtered[df_filtered['tahun_anggaran'] == selected_tahun]

if selected_satker != "Semua Satker":
    df_filtered = df_filtered[df_filtered['nama_satker'] == selected_satker]

# Metric Scorecards (Highlight atas)
st.markdown("---")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(label="Total Pagu (Anggaran)", value=f"Rp {df_filtered['pagu'].sum():,.0f}")
kpi2.metric(label="Total Realisasi", value=f"Rp {df_filtered['Total Realisasi'].sum():,.0f}")
serapan_persen = (df_filtered['Total Realisasi'].sum() / df_filtered['pagu'].sum() * 100) if df_filtered['pagu'].sum() > 0 else 0
kpi3.metric(label="Persentase Serapan", value=f"{serapan_persen:.2f} %")
jumlah_paket = df_filtered['nama_paket'].nunique() if 'nama_paket' in df_filtered.columns else len(df_filtered)
kpi4.metric(label="Jumlah Paket", value=f"{jumlah_paket:,.0f}".replace(",", "."))
st.markdown("---")

# --- ROW 1: Chart Top 5 Paket ---
# Chart 1 (Pagu vs Realisasi) dihapuskan sesuai permintaan
# st.markdown("---")
st.subheader("1. Top 5 Pagu dengan Paket Pagu Tertinggi")

if 'nama_paket' in df_filtered.columns:
    st.markdown("5 Nama Paket pengadaan dengan nilai alokasi anggaran terbesar beserta Satuan Kerjanya.")
    
    # Kumpulkan berdasarkan paket dan satker
    if 'nama_satker' in df_filtered.columns:
        top5_paket = df_filtered.groupby(['nama_satker', 'nama_paket'])['pagu'].sum().reset_index()
    else:
        top5_paket = df_filtered.groupby('nama_paket')['pagu'].sum().reset_index()
        top5_paket['nama_satker'] = "Tidak diketahui"
        
    top5_paket = top5_paket.nlargest(5, 'pagu').sort_values('pagu', ascending=True)
    top5_paket['pagu_formatted'] = top5_paket['pagu'].apply(format_rupiah)
    
    # Membuat label 2 baris (Keduanya dibiarkan utuh tanpa dipotong)
    def create_label(row):
        paket = str(row['nama_paket'])
        satker = str(row['nama_satker'])
        # Tampilkan teks secara utuh tanpa ada pemotongan panjang karakter
        return f"{paket}<br><i>({satker})</i>"
        
    top5_paket['nama_paket_label'] = top5_paket.apply(create_label, axis=1)
    
    # Horizontal Bar Chart
    fig2 = px.bar(top5_paket, x='pagu', y='nama_paket_label', orientation='h',
                  text='pagu_formatted', color_discrete_sequence=['#5b9bd5'],
                  hover_data={'nama_paket': True, 'nama_satker': True, 'nama_paket_label': False})
                  
    fig2.update_traces(textfont_size=12, textangle=0, textposition="outside")
    fig2.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Alokasi Pagu (Rp)", 
        yaxis_title="",
        margin=dict(l=20, r=20, t=30, b=40)
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Kolom 'nama_paket' tidak tersedia dalam data.")

# --- KOMPOSISI IDENTIFIKASI ---
st.markdown("---")
st.subheader("2. Komposisi Identifikasi Pembelian")

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
st.subheader("3. Analisis Pembelian Berulang")
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

# Menyusun kolom untuk grouping
group_cols = ['nama_satker']
if 'jenis_pengadaan' in df_rep_target.columns:
    group_cols.append('jenis_pengadaan')
if 'Jenis Belanja' in df_rep_target.columns:
    group_cols.append('Jenis Belanja')
group_cols.append(ident_col)

# Menghitung Frekuensi Pembelian berdasarkan grouping yang lebih detail
df_rep = df_rep_target.groupby(group_cols).size().reset_index(name='Frekuensi Transaksi')
df_rep_nilai = df_rep_target.groupby(group_cols)['pagu'].sum().reset_index()

# Gabung data frekuensi & nilai (menggunakan pagu bukan realisasi)
df_rep_final = pd.merge(df_rep, df_rep_nilai, on=group_cols)

# FILTER: Hanya tampilkan yang dibeli LEBIH DARI 1 KALI
df_rep_final = df_rep_final[df_rep_final['Frekuensi Transaksi'] > 1]
df_rep_final = df_rep_final.sort_values(by='Frekuensi Transaksi', ascending=False)

if not df_rep_final.empty:
    # Terapkan format Nominal Uang dengan cara menukar koma (ribuan dari Python) menjadi titik gaya Indonesia
    df_rep_final['Total Pagu (Rp)'] = df_rep_final['pagu'].apply(
        lambda x: f"Rp {x:,.0f}".replace(",", ".")
    )
    
    # Siapkan kolom yang akan ditampilkan
    display_cols = group_cols + ['Frekuensi Transaksi', 'Total Pagu (Rp)']
    
    # Tampilkan DataFrame dengan opsi custom styling pada Streamlit
    st.dataframe(
        df_rep_final[display_cols],
        use_container_width=True,
        column_config={
            'Frekuensi Transaksi': st.column_config.ProgressColumn(
                "Frekuensi", help="Total pengulangan pembelian",
                format="%f", min_value=0, max_value=int(df_rep_final['Frekuensi Transaksi'].max())
            ),
            'Total Pagu (Rp)': st.column_config.TextColumn(
                "Total Pagu"
            )
        },
        height=400,
        hide_index=True
    )
else:
    st.info("💡 Tidak ditemukan transaksi/pembelian yang dilakukan secara berulang (> 1 kali) pada filter ini.")
