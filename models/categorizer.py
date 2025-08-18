import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

@st.cache_resource
def get_sbert_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

class SmartCategorizer:
    def __init__(self,confidence_threshold=0.5):
        self.model = get_sbert_model()
        self.category_centroids={}
        self.confidence_threshold = confidence_threshold


    def fit(self,categorized_df: pd.DataFrame):
        print("Fitting SmartCategorizer: Learning from user's categories...")
        learn_df = categorized_df[categorized_df['category'] != "Uncategorized"]
        if learn_df.empty:
            print("No categorized data available to learn from. The model is not fitted.")
            return
        grouped_df = learn_df.groupby('category')
        for group_category, group_df in grouped_df:
            details_list = group_df['details'].tolist()
            embedding = self.model.encode(details_list)
            centroids = np.mean(embedding,axis=0)
            self.category_centroids[group_category]=centroids
        print(f"Fitting Complete. learned {len(self.category_centroids)} categories.")

    def predict(self, Uncategorized_details : list[str]) -> list[str]:
        if not self.category_centroids:
            return ['Uncategorized'] * len(Uncategorized_details)
        print(f"Predicting categories for {len(Uncategorized_details)} new transactions")
        new_embedding = self.model.encode(Uncategorized_details)
        category_name = list(self.category_centroids.keys())
        centroids_matrix = np.array(list(self.category_centroids.values()))
        similarity_matrix = cosine_similarity(new_embedding,centroids_matrix)
        predicted_categories=[]
        for i in range(len(Uncategorized_details)):
            best_match_score = np.max(similarity_matrix[i])
            if best_match_score >= self.confidence_threshold:
                best_match_index= np.argmax(similarity_matrix[i])
                predicted_categories.append(category_name[best_match_index])
            else:
                predicted_categories.append('Uncategorized')

        print('Prediction Complete')
        return predicted_categories