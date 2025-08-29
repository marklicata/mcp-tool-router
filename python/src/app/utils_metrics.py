import asyncio
import configparser
import json
import logging
import time
import http.client
import math
from collections import Counter
from typing import List, Dict, Any
import numpy as np
from pydantic.dataclasses import dataclass
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI, OpenAIError, embeddings
from utils_request_manager import RequestHandler
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class MetricsResult:
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    average_precision: float = 0.0
    ndcg_at_k: float = 0.0
    redundancy_score: float = 0.0
    confusion_index: float = 0.0

class MetricsCalculator:
    """Calculator for various metrics and measurements used in test evaluation."""
    def __init__(self, config: configparser.ConfigParser):
        """Initialize the MetricsCalculator with necessary configurations and clients."""
        self.config = config
        
        # Azure authentication
        self.credential = DefaultAzureCredential()
        self.token_provider = get_bearer_token_provider(self.credential, "https://cognitiveservices.azure.com/.default")

        # Azure OpenAI client
        self.az_openaoi_client = AzureOpenAI(
            api_version="2024-02-01",
            azure_endpoint="https://malicata-azure-ai-foundry.cognitiveservices.azure.com/",
            azure_ad_token_provider=self.token_provider,
        )

    async def precision_at_k(self, selected_tools: list[dict], expected_tools: list, k: int = 10) -> float:
        """
            Measures how well the search did at returning the expected names at the top of the returned tools list.
        """
        selected_tools = [f"{tool['server']}.{tool['name']}" for tool in selected_tools]
        selected_tools = selected_tools[:k]
        overlap = set(selected_tools) & set(expected_tools)
        return len(overlap) / len(expected_tools) if expected_tools else 0.0

    async def recall_at_k(self, selected_tools: list[dict], expected_tools: list, k: int) -> float:
        """
            Measures how many of the expected tools were selected.
        """
        selected_names = [f"{tool['server']}.{tool['name']}" for tool in selected_tools]
        overlap = set(expected_tools) & set(selected_names)
        return len(overlap) / len(expected_tools)


    async def average_precision(self, selected_tools: list, expected_names: list, k: int = 10) -> float:
        """
        Compute the average precision for the selected tools against expected tools.
        args:
            selected_tools: List of tools selected by the model.
            expected_tools: List of tools that were expected to be selected.
        returns:
            Average precision score as a float.
        """
        selected_names = [f"{tool['server']}.{tool['name']}" for tool in selected_tools]
        selected_names = selected_names[:k]
        hits = 0
        sum_precisions = 0.0
        for idx, tool in enumerate(selected_names, start=1):
            if tool in expected_names:
                hits += 1
                sum_precisions += hits / idx
        return sum_precisions / len(expected_names) if expected_names else 0.0        

    async def discounted_gain_at_k(self, selected_tools: list, expected_tools: list, k: int) -> float:
        ####
        # TODO: pass the number of tools we want returned to the server. Rather than coding in server config.
        ####
        """
        Compute the discounted cumulative gain (DCG) at k. Rewards putting highly relevant tools up front.
        """
        selected_names = [f"{tool['server']}.{tool['name']}" for tool in selected_tools]
        dcg = 0.0
        for i, tool in enumerate(selected_names[:k], start=1):
            rel = 1 if tool in expected_tools else 0
            dcg += (2**rel - 1) / math.log2(i + 1)
        return dcg

    async def ideal_discounted_gain_at_k(self, expected_tools: list, k: int) -> float:
        # ideal DCG is having all relevant items in the top positions
        ideal_relations = [1] * min(len(expected_tools), k)
        idcg = 0.0
        for i, rel in enumerate(ideal_relations, start=1):
            idcg += (2**rel - 1) / math.log2(i + 1)
        return idcg

    async def net_discounted_gain_at_k(self, selected_tools: list, expected_tools: list, k: int) -> float:
        idcg = await self.ideal_discounted_gain_at_k(expected_tools, k)
        dcg = await self.discounted_gain_at_k(selected_tools, expected_tools, k)
        return dcg / idcg if idcg > 0 else 0.0

    async def compute_redundancy_score_azure(self, selected_tools: dict) -> float:
        """
        - What it measures: Average semantic similarity between selected tools.
        - Why it matters: LLMs struggle to distinguish between tools that are too similar, leading to confusion or poor routing.
        """
        texts = [tool['desc'] for tool in selected_tools]
        try:
            response = self.az_openaoi_client.embeddings.create(
                input=texts,
                model="text-embedding-3-large"
            )
        except OpenAIError as e:
            logging.error(f"Error creating embeddings: {e}")
            return 0.0

        embeddings = [item.embedding for item in response.data]
        sim_matrix = cosine_similarity(embeddings)

        # Exclude diagonal
        n = len(texts)
        mask = np.ones((n, n)) - np.eye(n)
        avg_similarity = (sim_matrix * mask).sum() / (n * (n - 1))
        return avg_similarity

    async def compute_metrics(self, selected_tools: list[dict], expected_tools: list, top_k:int) -> MetricsResult:
        """Populate this object’s metrics fields."""
        m_result = MetricsResult(
            precision_at_k=await self.precision_at_k(selected_tools, expected_tools, 10),
            recall_at_k=await self.recall_at_k(selected_tools, expected_tools, 10),
            average_precision=await self.average_precision(selected_tools, expected_tools, 10),
            ndcg_at_k=await self.net_discounted_gain_at_k(selected_tools, expected_tools, top_k)
        )
        m_result.redundancy_score = await self.compute_redundancy_score_azure(selected_tools)
        m_result.confusion_index = len(selected_tools) * m_result.redundancy_score

        return m_result

    def generate_summary_statistics(self, test_results_list: list, 
                                   total_queries: int, total_time_start: float, 
                                   raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive summary statistics from test results."""
        # Overall statistics
        result_count = len(test_results_list)
        total_time = round((time.time() - total_time_start) * 1000, 2)  # in milliseconds

        # Performance statistics
        response_times = [r.response_time for r in test_results_list]
        tp50_query_time = round(np.percentile(response_times, 50), 2) if response_times else 0.0
        tp75_query_time = round(np.percentile(response_times, 75), 2) if response_times else 0.0
        tp90_query_time = round(np.percentile(response_times, 90), 2) if response_times else 0.0
        tp95_query_time = round(np.percentile(response_times, 95), 2) if response_times else 0.0

        # Match statistics
        matches = len([result for result in test_results_list if result.match])
        top_1_match = len([r for r in test_results_list if r.match_top_1])
        top_3_matches = len([r for r in test_results_list if r.match_top_3])
        top_5_matches = len([r for r in test_results_list if r.match_top_5])
        top_10_matches = len([r for r in test_results_list if r.match_top_10])
    
        # Selection ENABLED Scores
        selection_enabled_precision = [r.selection_enabled_metrics['precision_at_k'] for r in test_results_list if r.selection_enabled_metrics]
        selection_enabled_recall = [r.selection_enabled_metrics['recall_at_k'] for r in test_results_list if r.selection_enabled_metrics]
        selection_enabled_average_precision = [r.selection_enabled_metrics['average_precision'] for r in test_results_list if r.selection_enabled_metrics]
        selection_enabled_ndcg = [r.selection_enabled_metrics['ndcg_at_k'] for r in test_results_list if r.selection_enabled_metrics]
        selection_enabled_redundancy_score = [r.selection_enabled_metrics['redundancy_score'] for r in test_results_list if r.selection_enabled_metrics]
        selection_enabled_confusion_index = [r.selection_enabled_metrics['confusion_index'] for r in test_results_list if r.selection_enabled_metrics]

        # Average Selection ENABLED Scores
        avg_selection_enabled_precision = (sum(selection_enabled_precision) / len(selection_enabled_precision)) if selection_enabled_precision else 0.0
        avg_selection_enabled_recall = (sum(selection_enabled_recall) / len(selection_enabled_recall)) if selection_enabled_recall else 0.0
        avg_selection_enabled_average_precision = (sum(selection_enabled_average_precision) / len(selection_enabled_average_precision)) if selection_enabled_average_precision else 0.0
        avg_selection_enabled_ndcg = (sum(selection_enabled_ndcg) / len(selection_enabled_ndcg)) if selection_enabled_ndcg else 0.0
        avg_selection_enabled_redundancy_score = (sum(selection_enabled_redundancy_score) / len(selection_enabled_redundancy_score)) if selection_enabled_redundancy_score else 0.0
        avg_selection_enabled_confusion_index = (sum(selection_enabled_confusion_index) / len(selection_enabled_confusion_index)) if selection_enabled_confusion_index else 0.0

        # Selection DISABLED Scores
        selection_disabled_precision = [r.selection_disabled_metrics['precision_at_k'] for r in test_results_list if r.selection_disabled_metrics]
        selection_disabled_recall = [r.selection_disabled_metrics['recall_at_k'] for r in test_results_list if r.selection_disabled_metrics]
        selection_disabled_average_precision = [r.selection_disabled_metrics['average_precision'] for r in test_results_list if r.selection_disabled_metrics]
        selection_disabled_ndcg = [r.selection_disabled_metrics['ndcg_at_k'] for r in test_results_list if r.selection_disabled_metrics]
        selection_disabled_redundancy_score = [r.selection_disabled_metrics['redundancy_score'] for r in test_results_list if r.selection_disabled_metrics]
        selection_disabled_confusion_index = [r.selection_disabled_metrics['confusion_index'] for r in test_results_list if r.selection_disabled_metrics]

        # Average Selection DISABLED Scores
        avg_selection_disabled_precision = (sum(selection_disabled_precision) / len(selection_disabled_precision)) if selection_disabled_precision else 0.0
        avg_selection_disabled_recall = (sum(selection_disabled_recall) / len(selection_disabled_recall)) if selection_disabled_recall else 0.0
        avg_selection_disabled_average_precision = (sum(selection_disabled_average_precision) / len(selection_disabled_average_precision)) if selection_disabled_average_precision else 0.0
        avg_selection_disabled_ndcg = (sum(selection_disabled_ndcg) / len(selection_disabled_ndcg)) if selection_disabled_ndcg else 0.0
        avg_selection_disabled_redundancy_score = (sum(selection_disabled_redundancy_score) / len(selection_disabled_redundancy_score)) if selection_disabled_redundancy_score else 0.0
        avg_selection_disabled_confusion_index = (sum(selection_disabled_confusion_index) / len(selection_disabled_confusion_index)) if selection_disabled_confusion_index else 0.0


        stats = {
            'total_queries': total_queries,
            'result_count': result_count,
            'total_time': total_time,
            'tp50_query_time': tp50_query_time,
            'tp75_query_time': tp75_query_time,
            'tp90_query_time': tp90_query_time,
            'tp95_query_time': tp95_query_time,
            'matches': matches,
            'top_1_match': top_1_match,
            'top_3_matches': top_3_matches,
            'top_5_matches': top_5_matches,
            'top_10_matches': top_10_matches,
            'metrics_table': {
                "Precision@K": {
                    "Description": "Measures how many of the top-K selected tools are actually relevant. High precision means more relevant tools are surfaced in the shortlist.",
                    "Range": "0.0 - 1.0",
                    "Selection Enabled": avg_selection_enabled_precision,
                    "Selection Disabled": avg_selection_disabled_precision
                },
                "Recall@K": {
                    "Description": "Measures how many of the relevant tools were successfully retrieved in the top-K list. High recall means you're capturing most of what matters.",
                    "Range": "0.0 - 1.0",
                    "Selection Enabled": avg_selection_enabled_recall,
                    "Selection Disabled": avg_selection_disabled_recall
                },
                "Average Precision": {
                    "Description": "A ranking-sensitive metric that rewards placing relevant tools earlier in the list. It averages precision at each point a relevant tool is found.",
                    "Range": "0.0 - 1.0",
                    "Selection Enabled": avg_selection_enabled_average_precision,
                    "Selection Disabled": avg_selection_disabled_average_precision
                },
                "nDCG@K": {
                    "Description": "Normalized Discounted Cumulative Gain. Rewards placing relevant tools higher in the ranking, with diminishing returns for lower-ranked hits.",
                    "Range": "0.0 - 1.0",
                    "Selection Enabled": avg_selection_enabled_ndcg,
                    "Selection Disabled": avg_selection_disabled_ndcg
                },
                "Redundancy Score": {
                    "Description": "Measures semantic similarity among selected tools. High scores indicate many tools are too similar, which can confuse LLMs during selection.",
                    "Range": "0.0 - 1.0",
                    "Selection Enabled": avg_selection_enabled_redundancy_score,
                    "Selection Disabled": avg_selection_disabled_redundancy_score
                },
                "Confusion Index": {
                    "Description": "Combines list length and redundancy to estimate cognitive load on the LLM. High values suggest the model may struggle to make confident, distinct choices",
                    "Range": "0.0 - inf",
                    "Selection Enabled": avg_selection_enabled_confusion_index,
                    "Selection Disabled": avg_selection_disabled_confusion_index
                }
            }
        }

        return stats