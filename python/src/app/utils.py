import asyncio, configparser, time, sys, os, json, random, logging, math, http.client
from collections import Counter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI, OpenAIError
from typing import List, Dict, Any, Optional
from pydantic.dataclasses import dataclass
from tabulate import tabulate



@dataclass
class TestResult:
    """Dataclass to store the result of a test case."""
    expected_tools: List[str]
    matching_tools: List[str]
    missing_tools: List[str]
    unexpected_tools: List[str]
    returned_tools: List[str]
    query: str = ""
    response_time: float = 0.0
    match: bool = False
    match_top_1: bool = False
    match_top_3: bool = False
    match_top_5: bool = False
    match_top_10: bool = False
    precision_metric: float = 0.0
    recall_metric: float = 0.0
    judge_metric: float = 0.0


@dataclass
class TestCase:
    """Dataclass to store the information of a test case."""
    question: str
    description: str
    expected_tools: list[str]

class RequestHandler:
    def __init__(self):
        self.headers = {
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Authorization': f"Bearer None",
            'content-type': 'application/json'
        }       

    def route_request(self, query: str) -> str:
        self.conn = http.client.HTTPConnection("localhost", 8000)
        payload = json.dumps({'query': query})

        try:
            self.conn.request("PUT", f"/get_mcp_tools/", payload, self.headers)
            res = self.conn.getresponse()
            data = res.read()
            result_str = data.decode("utf-8")
            if res.will_close:
                self.conn.close()
                self.conn = http.client.HTTPConnection("localhost", 8000)  # Reinitialize connection if it was closed
        except Exception as e:
            print(f"Error occurred: {e}")
            result_str = None
        return result_str

class TestRunManager:
    """Manager for running test cases and evaluating tool selection quality."""

    def __init__(self):
        """Initialize the TestRunManager with necessary configurations and clients."""
        self.request_handler = RequestHandler()

        # Load configuration
        self.config = configparser.ConfigParser()
        self.config.read('python/src/app/data/config.ini')
        
        # Azure authentication
        self.credential = DefaultAzureCredential()
        self.token_provider = get_bearer_token_provider(self.credential, "https://cognitiveservices.azure.com/.default")

        # Azure OpenAI client
        self.az_openaoi_client = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint="https://malicata-azure-ai-foundry.cognitiveservices.azure.com/",
            azure_ad_token_provider=self.token_provider,
        )
    
    async def _calculate_precision(self, selected_tools: list, expected_tools: list) -> float:
        """
        Calculate precision for the selected tools against expected tools.
        Precision = True Positives / (True Positives + False Positives)
        """
        true_positives = len([tool for tool in selected_tools if tool in expected_tools])
        false_positives = len([tool for tool in selected_tools if tool not in expected_tools])
        
        if true_positives + false_positives == 0:
            return 0.0
        return round(true_positives / (true_positives + false_positives), 2)
    
    async def _calculate_recall(self, selected_tools: list, expected_tools: list) -> float:
        """
        Calculate recall for the selected tools against expected tools.
        Recall = True Positives / (True Positives + False Negatives)
        """
        true_positives = len([tool for tool in selected_tools if tool in expected_tools])
        false_negatives = len([tool for tool in expected_tools if tool not in selected_tools])
        
        if true_positives + false_negatives == 0:
            return 0.0
        return round(true_positives / (true_positives + false_negatives), 2)

    async def _calculate_judgement(self, query: str, selected_tools: list, expected_tools: list) -> float:
        async def get_judge_score() -> float:
            try:
                result = self.az_openaoi_client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {
                            "role": "system",
                            "content": 
                                "You are a helpful assistant that helps evaluate if the correct TOOLS have been selected to help an LLM answer the user's prompt."
                                "You will be given the user's prompt. And then a json array of tools that were selected to help answer the prompt. Each tool will include a name and description."
                                "I would like you to rate how well the selected tools would help answer the prompt on a scale of 1-10, where 0 is completely useless and 10 is perfect."
                                "You will provide this score in simple JSON format: {'score': <number from 0-10>}"
                                "That is it. Provide no other commentary or text."
                        },
                        {
                            "role": "user",
                            "content": f"Query: {query}. \nTools: {selected_tools}. "
                        }
                    ],
                    temperature=0,
                    max_completion_tokens=800,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
                result_str = result.choices[0].message.content
                score = json.loads(result_str.replace("'", '"')).get('score', '')
                return score
            except OpenAIError as e:
                print(f"OpenAI error: {e}")
                return None

        tasks = []
        for i in range(0, self.config.getint('TestRun', 'TOOL_QUALITY_JUDGES', fallback=5)):
            tasks.append(get_judge_score())
        scores = await asyncio.gather(*tasks)
        valid_scores = [s for s in scores if s is not None]
        if len(valid_scores) > 0:
            return round((sum(valid_scores) / len(valid_scores)), 2) if valid_scores else None
        else:
            return 0.0

    async def run_single_test(self, test_case: TestCase, index: int) -> None:
        print(f"Running test case #{index}: {test_case.question}")

        # Adding app criteria to the query as an example of user context. Assuming server name and app name are the same.
        query = f"Current application: {test_case.expected_tools[0].split('.')[0]}. {test_case.question}"
        results_json = self.request_handler.route_request(query=query)

        if results_json is not None and results_json != "":
            results_json = json.loads(results_json)
        else:
            print(f"Error: No response received for query: {test_case.question}")
            return None


        returned_tools=[f"{tool.get('server', '')}.{tool.get('name', '')}" for tool in results_json.get('tools', [])]
        matching_tools=[tool for tool in returned_tools if tool in test_case.expected_tools]
        unexpected_tools=[tool for tool in returned_tools if tool not in test_case.expected_tools]
        missing_tools=[tool for tool in test_case.expected_tools if tool not in returned_tools]


        # Generate initial test result
        single_test_result = TestResult(
            query=test_case.question,
            response_time=results_json.get('execution_time', 0)*1000,  # Convert to milliseconds
            returned_tools=returned_tools,
            expected_tools=test_case.expected_tools,
            matching_tools=matching_tools,
            unexpected_tools=unexpected_tools,
            missing_tools=missing_tools
        )

        # Calculate precision, recall, and judgement metrics
        single_test_result.precision_metric = await self._calculate_precision(returned_tools, test_case.expected_tools)
        single_test_result.recall_metric = await self._calculate_recall(returned_tools, test_case.expected_tools)
        single_test_result.judge_metric = await self._calculate_judgement(query=test_case.question, selected_tools=returned_tools, expected_tools=test_case.expected_tools)

        # Calculate top matches
        if len(single_test_result.matching_tools) > 0:
            single_test_result.match = True
        if any(item in returned_tools for item in test_case.expected_tools[:1]):
            single_test_result.match_top_1 = True
        elif any(item in returned_tools for item in test_case.expected_tools[:3]):
            single_test_result.match_top_3 = True
        elif any(item in returned_tools for item in test_case.expected_tools[:5]):
            single_test_result.match_top_5 = True
        elif any(item in returned_tools for item in test_case.expected_tools[:10]):
            single_test_result.match_top_10 = True

        with open("python/src/app/data/test_results.json", "r", encoding="utf-8") as file:
            try:
                existing_results = json.load(file)
            except json.JSONDecodeError:
                existing_results = []

        existing_results.append(single_test_result.__dict__)
        
        with open("python/src/app/data/test_results.json", "w", encoding="utf-8") as f:
            json.dump(existing_results, f, indent=4, ensure_ascii=False)


    async def run_multiple_test_cases(self, count: int = 0):
        """
        Run multiple test cases and evaluate tool selection quality.
        Args:
            count (int): The number of test cases to run. If 0, uses the sample size from the config."
        """

        total_time_start = time.time()

        with open('python/src/app/data/test_cases.json', 'r', encoding='utf-8') as file:
            raw_tests = json.load(file)

        random.shuffle(raw_tests)

        # if a specific count is not provided, use the sample size from config
        if count == 0:
            trimmed_tests = raw_tests[:self.config.getint('TestRun', 'SAMPLE_SIZE')]
        else:
            trimmed_tests = raw_tests[:count]

        tasks = []
        i = 1
        for test in trimmed_tests:
            test_case = TestCase(
                question=test['question'],
                description=test['description'],
                expected_tools=test['expected_tools']
            )
            tasks.append(self.run_single_test(test_case, i))
            i += 1
        await asyncio.gather(*tasks)
        
        ####
        print(f"\n\n====TEST RUN COMPLETE====\n")
        print(f"Total test cases run: {len(trimmed_tests)}")
        print(f"Total time taken: {round((time.time() - total_time_start) * 1000, 2)} ms")
        print(f"Test results saved to: python/src/app/data/test_results.json\n")
        print(f"Creating results summary...\n")
        ####

        test_results_list = []
        with open("python/src/app/data/test_results.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        test_results_list = [TestResult(**item) for item in data]
        
        # Overall statistics
        total_queries = len(trimmed_tests)
        result_count = len(test_results_list)
        total_time = round((time.time() - total_time_start) * 1000, 2)  # in milliseconds
        avg_query_time = round(sum([r.response_time for r in test_results_list]) / total_queries, 2) if total_queries > 0 else 0.0
        matches = len([result for result in test_results_list if result.match])
        top_1_match = len([r for r in test_results_list if r.match_top_1])
        top_3_matches = len([r for r in test_results_list if r.match_top_3])
        top_5_matches = len([r for r in test_results_list if r.match_top_5])
        top_10_matches = len([r for r in test_results_list if r.match_top_10])

        valid_precision_scores = [r.precision_metric for r in test_results_list if r.precision_metric is not None]
        valid_recall_scores = [r.recall_metric for r in test_results_list if r.recall_metric is not None]
        valid_judge_scores = [r.judge_metric for r in test_results_list if r.judge_metric is not None]

        avg_precision_score = (sum(valid_precision_scores) / len(valid_precision_scores)) * 100 if valid_precision_scores else 0.0
        avg_recall_score = (sum(valid_recall_scores) / len(valid_recall_scores)) * 100 if valid_recall_scores else 0.0
        avg_judge_score = round(sum(valid_judge_scores) / len(valid_judge_scores), 2) if valid_judge_scores else 0.0

        print(f"\n====TEST RUN SUMMARY====")
        print(f"Total queries processed: {total_queries}")
        print(f"Successful queries: {result_count}")
        print(f"Failed queries: {total_queries - result_count}")
        print(f"Average time per query: {avg_query_time:.2f} ms")
        print(f"\n====TOOL SELECTION QUALITY====")
        print(f"Match success rate: {matches/result_count*100:.1f}% ({matches})")
        print(f"Match miss rate: {(result_count-matches)/result_count*100:.1f}% ({(result_count-matches)})")
        print(f"Top match: {top_1_match} ({(top_1_match / matches * 100):.1f}%)" if matches else f"Top match: {top_1_match}")
        print(f"Top 3 matches: {top_3_matches} ({top_3_matches/matches*100:.1f}%)" if matches else f"Top 3 matches: {top_3_matches}")
        print(f"Top 5 matches: {top_5_matches} ({top_5_matches/matches*100:.1f}%)" if matches else f"Top 5 matches: {top_5_matches}")
        print(f"Top 10 matches: {top_10_matches} ({top_10_matches/matches*100:.1f}%)" if matches else f"Top 10 matches: {top_10_matches}")
        print(f"\n====TOOL SELECTION ACCURACY====")
        print(f"Average Precision Score: {avg_precision_score:.1f}%***")
        print(f"Average Recall Score: {avg_recall_score:.1f}%")
        print(f"Average Judge Score: {avg_judge_score:.2f}")
        print(f"\n====MISSED TOOLS====")

        data = [["Expected Tools", "Returned Tools", "Query"]]
        for result in test_results_list:
            if len(result.missing_tools) > 0:
                print(f"Expected tools: {result.expected_tools}, Returned tools: {result.returned_tools}, Query: {result.query}")

        print(f"\n***Note: precision will not work well until we expect multiple tools to be returned.***\n")