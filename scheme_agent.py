import chromadb
from chromadb.utils import embedding_functions

CHROMA_DIR = "./scheme_db"

SCHEMES = [
    {
        "id": "pm_kisan",
        "text": (
            "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi): Provides income support "
            "of Rs 6,000 per year to all landholding farmer families, paid in three "
            "equal installments of Rs 2,000 every four months, directly to bank "
            "accounts. Eligibility: all landholding farmers, subject to certain "
            "exclusions (income tax payers, institutional landholders, government "
            "employees above a certain grade). Apply via pmkisan.gov.in or through "
            "the local Common Service Centre (CSC) with Aadhaar and land records."
        ),
    },
    {
        "id": "pmfby",
        "text": (
            "PMFBY (Pradhan Mantri Fasal Bima Yojana): Crop insurance scheme "
            "protecting farmers against crop loss due to natural calamities, pests, "
            "or disease. Farmer premium is capped at 2% of sum insured for Kharif "
            "crops, 1.5% for Rabi crops, and 5% for commercial/horticultural crops "
            "-- the rest is subsidized by government. Covers pre-sowing to "
            "post-harvest losses. Apply through banks, insurance companies, CSCs, "
            "or the National Crop Insurance Portal before the season's cutoff date."
        ),
    },
    {
        "id": "kcc",
        "text": (
            "KCC (Kisan Credit Card): Provides farmers with affordable, timely "
            "credit for crop cultivation, post-harvest expenses, and farm asset "
            "maintenance. Interest rate is subsidized to around 4% per annum for "
            "loans up to Rs 3 lakh if repaid on time (includes interest subvention "
            "and prompt repayment incentive). Valid for 5 years with annual review. "
            "Apply at any nationalized bank, regional rural bank, or cooperative "
            "bank with land documents and identity proof."
        ),
    },
    {
        "id": "soil_health_card",
        "text": (
            "Soil Health Card Scheme: Provides farmers with a report on their "
            "soil's nutrient status (N, P, K, and other micronutrients) along with "
            "crop-wise fertilizer and soil amendment recommendations. Cards are "
            "issued once every 2 years, free of cost, by testing soil samples at "
            "government labs. Helps farmers use fertilizers more efficiently and "
            "reduce input costs. Contact the local Krishi Vigyan Kendra (KVK) or "
            "agriculture department office to get soil tested."
        ),
    },
    {
        "id": "pm_kusum",
        "text": (
            "PM-KUSUM (Pradhan Mantri Kisan Urja Suraksha evam Utthaan Mahabhiyan): "
            "Promotes solar energy use in agriculture -- subsidizes solar pumps "
            "(up to 60% subsidy) and supports setting up small solar power plants "
            "on barren land, allowing farmers to sell surplus power to the grid. "
            "Reduces dependence on diesel pumps and provides an additional income "
            "source. Apply through state renewable energy department or DISCOM."
        ),
    },
    {
        "id": "enam",
        "text": (
            "e-NAM (National Agriculture Market): An online trading platform "
            "connecting existing APMC mandis to create a unified national market "
            "for agricultural commodities. Lets farmers get better price discovery "
            "and sell produce to buyers beyond their local mandi. Free registration "
            "for farmers through the local APMC mandi or the eNAM mobile app; "
            "requires linking bank account and land records."
        ),
    },
]


def get_client():
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name="schemes", embedding_function=embed_fn
    )
    return collection


def build_index():
    collection = get_client()
    collection.upsert(
        ids=[s["id"] for s in SCHEMES],
        documents=[s["text"] for s in SCHEMES],
    )
    print(f"Indexed {len(SCHEMES)} schemes into {CHROMA_DIR}")


def query_schemes(question, top_k=2):
    collection = get_client()
    results = collection.query(query_texts=[question], n_results=top_k)
    docs = results["documents"][0]
    return docs


if __name__ == "__main__":
    build_index()
    print("\n--- Test query: 'insurance for crop damage' ---")
    for doc in query_schemes("insurance for crop damage"):
        print(doc[:150], "...\n")
