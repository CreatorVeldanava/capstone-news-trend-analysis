from pathlib import Path
from bertopic import BERTopic

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR
    / "outputs"
    / "preprocessing_experiments"
    / "protected_terms_model"
    / "model"
)

print("=" * 60)
print("PEMERIKSAAN MODEL BERTopic - PROTECTED TERMS")
print("=" * 60)

print("Lokasi model:", MODEL_PATH)
print("Folder tersedia:", MODEL_PATH.exists())

try:
    topic_model = BERTopic.load(
        str(MODEL_PATH),
        embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )

    print("\nMODEL BERHASIL DIMUAT")
    print("Jumlah topik:", len(topic_model.get_topic_info()) - 1)

    topic_info = topic_model.get_topic_info()

    print("\nCONTOH INFORMASI TOPIK:")
    print(topic_info.head(6).to_string(index=False))

except Exception as error:
    print("\nMODEL GAGAL DIMUAT")
    print("Jenis error:", type(error).__name__)
    print("Pesan:", error)