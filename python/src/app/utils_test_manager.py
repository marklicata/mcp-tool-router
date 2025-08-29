import asyncio
import configparser
import time
import sys
import os
import json
import random
import logging
import random
from collections import Counter
from typing import List
from dataclasses import dataclass, asdict
from utils_metrics import MetricsCalculator, MetricsResult
from utils_request_manager import RequestHandler
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
    selection_enabled_metrics: MetricsResult = None
    selection_disabled_metrics: MetricsResult = None


@dataclass
class TestCase:
    """Dataclass to store the information of a test case."""
    question: str
    expected_tools: list[str]  


class TestRunManager:
    """Manager for running test cases and evaluating tool selection quality."""

    def __init__(self, request_handler=None):
        """Initialize the TestRunManager with necessary configurations and clients."""
        if request_handler is None:
            self.request_handler = RequestHandler()
        else:
            self.request_handler = request_handler

        # Load configuration
        self.config = configparser.ConfigParser()
        self.config.read('python/src/app/data/config.ini')
        
        # Initialize metrics calculator
        self.metrics_calculator = MetricsCalculator(self.config)

    async def run_single_test(self, test_case: TestCase, index: int) -> None:
        print(f"Running test case #{index}: {test_case.question}")

        # Adding app criteria to the query as an example of user context. Assuming server name and app name are the same.
        query = f"Current application: {test_case.expected_tools[0].split('.')[0]}. {test_case.question}"
        results_json = self.request_handler.route_request(query=query, url="/get_mcp_tools/")

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
        metrics_calculator = MetricsCalculator(self.config)


        selected_tools_for_metrics_calc = [{"server": f"{tool.get('server', '')}", "name": f"{tool.get('name', '')}", "desc": f"{tool.get('description', '')}"} for tool in results_json.get('tools') or []]

        single_test_result.selection_enabled_metrics = await metrics_calculator.compute_metrics(
            selected_tools=selected_tools_for_metrics_calc,
            expected_tools=test_case.expected_tools,
            top_k=len(returned_tools)
        )

        if self.config.getboolean('TestRun', 'RUN_SIMPLE_SEARCH_COMPARISON', fallback=False):
            try:
                search_result_json = self.request_handler.route_request(query=query, url="/run_az_search/")
            except Exception as e:
                print(f"Error occurred while running search comparison: {e}")
            if search_result_json is not None and search_result_json != "":
                search_result_json = json.loads(search_result_json)
            else:
                print(f"Error: No response received for query: Az Search using query: {query}")
                return None
            search_result_tools_for_metrics_calc = [{"server": f"{tool.get('server', '')}", "name": f"{tool.get('name', '')}", "desc": f"{tool.get('description', '')}"} for tool in search_result_json.get('tools', [])]
            random.shuffle(search_result_tools_for_metrics_calc)
            single_test_result.selection_disabled_metrics = await metrics_calculator.compute_metrics(
                selected_tools=search_result_tools_for_metrics_calc,
                expected_tools=test_case.expected_tools,
                top_k=len(search_result_tools_for_metrics_calc)
            )

        with open("python/src/app/data/test_results.json", "r", encoding="utf-8") as file:
            try:
                existing_results = json.load(file)
            except json.JSONDecodeError:
                existing_results = []

        existing_results.append(asdict(single_test_result))

        with open("python/src/app/data/test_results.json", "w", encoding="utf-8") as f:
            json.dump(existing_results, f, indent=4, ensure_ascii=False)


    async def run_multiple_test_cases(self, count: int = 0):
        """
        Run multiple test cases and evaluate tool selection quality.
        Args:
            count (int): The number of test cases to run. If 0, uses the sample size from the config."
        """
        total_time_start = time.time()

        # Clear the test results file before starting
        with open("python/src/app/data/test_results.json", "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

        # Load test cases from the specified file
        test_case_file = self.config.get('TestRun', 'TEST_CASE_FILE', fallback='python/src/app/data/test_cases_simple_100_M365.json')        
        with open(test_case_file, 'r', encoding='utf-8') as file:
            raw_tests = json.load(file)

        random.shuffle(raw_tests)

        # Set up the number of test runs based on the provided count, config, and number of tests available.
        if count == 0 and len(raw_tests) > self.config.getint('TestRun', 'SAMPLE_SIZE', fallback=500):
            trimmed_tests = raw_tests[:self.config.getint('TestRun', 'SAMPLE_SIZE')]
        elif count > 0 and len(raw_tests) > count:
            trimmed_tests = raw_tests[:count]
        else:
            trimmed_tests = raw_tests

        tasks = []
        i = 1
        for test in trimmed_tests:
            test_case = TestCase(
                question=test['question'],
                expected_tools=test['expected_tools']
            )
            tasks.append(self.run_single_test(test_case, i))
            i += 1
        await asyncio.gather(*tasks)
        
        # Generate and print results summary
        await self._print_results_summary(trimmed_tests, total_time_start)


    async def _print_results_summary(self, trimmed_tests: List[dict], total_time_start: float):
        """Print comprehensive test results summary."""
        print(f"\n\n====TEST RUN COMPLETE====\n")
        print(f"Total test cases run: {len(trimmed_tests)}")
        print(f"Total time taken: {round((time.time() - total_time_start), 2)} seconds")
        print(f"Test results saved to: python/src/app/data/test_results.json\n")
        print(f"Creating results summary...\n")

        # Load test results
        test_results_list = []
        with open("python/src/app/data/test_results.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        
        # Create TestResult objects, handling optional fields gracefully
        for item in data:
            # Remove extra fields that aren't in TestResult if they exist
            test_result_data = {k: v for k, v in item.items() if k in TestResult.__dataclass_fields__}
            test_results_list.append(TestResult(**test_result_data))
        
        # Generate and print summary statistics
        summary_stats = self.metrics_calculator.generate_summary_statistics(
            test_results_list, len(trimmed_tests), total_time_start, data
        )
        self._print_summary_statistics(summary_stats, test_results_list)


    def _print_summary_statistics(self, stats: dict, test_results_list: List[TestResult]):
        """Print formatted summary statistics."""
        print(f"\n====TEST RUN SUMMARY====")
        print(f"Total queries processed: {stats['total_queries']}")
        print(f"Successful queries: {stats['result_count']}")
        print(f"Failed queries: {stats['total_queries'] - stats['result_count']}")
        print(f"TP50 response time: {stats['tp50_query_time']:.2f} ms")
        print(f"TP75 response time: {stats['tp75_query_time']:.2f} ms")
        print(f"TP90 response time: {stats['tp90_query_time']:.2f} ms")
        print(f"TP95 response time: {stats['tp95_query_time']:.2f} ms")
        print(f"\n====TOOL SELECTION QUALITY====")
        print(f"Match success rate: {stats['matches']/stats['result_count']*100:.1f}% ({stats['matches']})")
        print(f"Match miss rate: {(stats['result_count']-stats['matches'])/stats['result_count']*100:.1f}% ({(stats['result_count']-stats['matches'])})")
        print(f"Matches in first slot: {stats['top_1_match']} ({(stats['top_1_match'] / stats['matches'] * 100):.1f}%)" if stats['matches'] else f"Matches in first slot: {stats['top_1_match']}")
        print(f"Matches in top 3: {stats['top_3_matches']} ({stats['top_3_matches']/stats['matches']*100:.1f}%)" if stats['matches'] else f"Matches in top 3: {stats['top_3_matches']}")
        print(f"Matches in top 5: {stats['top_5_matches']} ({stats['top_5_matches']/stats['matches']*100:.1f}%)" if stats['matches'] else f"Matches in top 5: {stats['top_5_matches']}")
        print(f"Matches in top 10: {stats['top_10_matches']} ({stats['top_10_matches']/stats['matches']*100:.1f}%)" if stats['matches'] else f"Matches in top 10: {stats['top_10_matches']}")
        print(f"\n====TOOL SELECTION ACCURACY====")
        metrics_table = stats.get('metrics_table', {})
        # Convert to list of rows
        table_rows = [
            [metric, f"{values['Description']}", f"{values['Range']}", f"{values['Selection Enabled']:.4f}", f"{values['Selection Disabled']:.4f}"]
            for metric, values in metrics_table.items()
        ]
        print(tabulate(table_rows, headers=["Metric", "Description", "Range", "Selection Enabled", "Selection Disabled"], tablefmt="github"))
        print(f"\n====COMMONLY MISSED TOOLS====")
        # Calculate missed tools statistics
        missed_tools_cnt = 0
        test_case_with_missed_tools = 0
        missed_tools = {}
        for result in test_results_list:
            if len(result.missing_tools) > 0:
                missed_tools_cnt += len(result.missing_tools)
                test_case_with_missed_tools += 1
                for tool in result.missing_tools:
                    if tool not in missed_tools:
                        missed_tools[tool] = 1
                    else:
                        missed_tools[tool] += 1
        
        print(f"Test cases missing tools: {test_case_with_missed_tools} ({(test_case_with_missed_tools/stats['result_count']*100):.1f}%)")
        print(f"Average missing tools per test case: {missed_tools_cnt / test_case_with_missed_tools if test_case_with_missed_tools > 0 else 0:.2f}")
