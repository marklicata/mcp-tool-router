import asyncio, configparser, time, sys, os, json, random
from collections import Counter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.server.run import ToolRouter

config = configparser.ConfigParser()
config.read('python/src/app/data/config.ini')

tool_router = ToolRouter()

def run_single_query():
    while query is not None and query != "":
        start_time = time.time()
        try:
            results = asyncio.run(tool_router.route(
                query=query
            ))
        except Exception as e:
            print(f"Error occurred: {e}")
            results = None

        print("\n")
        for tool in results.tools:
            print(f"Server: {tool.server.name}, Tool: {tool.name}, Score: {tool.score:.2f}")
        print(f"Execution time: {(time.time() - start_time) * 100:.2f} ms\n")

        query = input("Type a new query or press Enter to exit... ")

async def test_run():

    async def run_single_test(query: str) -> dict:
        result = await tool_router.route(query=test['question'])
        # Get the 1-n tools that were returned. AND format in the format "server.tool"
        selected_tools_list = [f"{tool.server.name}.{tool.name}" for tool in result.tools]
        expected_tools_list = test.get('expected_tools', [])
        match_types = [1, 3, 5, 10]

        results_dict = {
            'match': False,
            'match_top_1': False,
            'match_top_3': False,
            'match_top_5': False,
            'match_top_10': False,
            'expected_tools': expected_tools_list,
            'matching_tools': [],
            'missing_tools': [],
            'unexpected_tools': [],
            'query': query,
        }

        if any(item in selected_tools_list[:1] for item in expected_tools_list):
            results_dict[f'match'] = True
            results_dict[f'match_top_1'] = True
            results_dict[f'match_top_3'] = False
            results_dict[f'match_top_5'] = False
            results_dict[f'match_top_10'] = False
        elif any(item in selected_tools_list[:3] for item in expected_tools_list):
            results_dict[f'match'] = True
            results_dict[f'match_top_1'] = False
            results_dict[f'match_top_3'] = True
            results_dict[f'match_top_5'] = False
            results_dict[f'match_top_10'] = False
        elif any(item in selected_tools_list[:5] for item in expected_tools_list):
            results_dict[f'match'] = True
            results_dict[f'match_top_1'] = False
            results_dict[f'match_top_3'] = False
            results_dict[f'match_top_5'] = True
            results_dict[f'match_top_10'] = False
        elif any(item in selected_tools_list[:10] for item in expected_tools_list):
            results_dict[f'match'] = True
            results_dict[f'match_top_1'] = False
            results_dict[f'match_top_3'] = False
            results_dict[f'match_top_5'] = False
            results_dict[f'match_top_10'] = True

        # 1-n tools that matched
        results_dict['matching_tools'] = [i for i in selected_tools_list if i in expected_tools_list]

        # 1-n tools in EXPECTED but missing from SELECTED
        results_dict['missing_tools'] = [i for i in expected_tools_list if i not in selected_tools_list]

        # 1-n tools in SELECTED but not in EXPECTED
        results_dict['unexpected_tools'] = [i for i in selected_tools_list if i not in expected_tools_list]

        return results_dict


    test_start = time.time()
    with open('python/src/app/data/test_cases.json', 'r') as file:
        raw_tests = json.load(file)

    if not tool_router.use_local_tools:
        filtered_tests = [q for q in raw_tests if not q['local_server']]
    else:
        filtered_tests = raw_tests

    random.shuffle(filtered_tests)
    filtered_tests = filtered_tests[:config.getint('TestRun', 'SAMPLE_SIZE')]

    results = []
    for test in filtered_tests:
        query = test['question']
        results_dict = await run_single_test(query)
        # Append the new block
        results.append(results_dict)


    total_time = time.time() - test_start

    # Overall statistics
    total_queries = len(results)
    top_1_match = len([r for r in results if r['match_top_1']])
    top_3_matches = len([r for r in results if r['match_top_3']])
    top_5_matches = len([r for r in results if r['match_top_5']])
    top_10_matches = len([r for r in results if r['match_top_10']])

    matches = len([results['match'] for results in results if results.get('match')])
    misses = total_queries - matches
    successful_queries = len([r for r in results if 'error' not in r])
    cache_hits = len([r for r in results if r.get('cache_hit', False)])
    # missing = [r.get('missing_tools') for r in results if r.get('missing_tools')]

    print(f"\n====TEST RUN SUMMARY====")
    print(f"Total queries processed: {total_queries}")
    print(f"Successful queries: {successful_queries}")
    print(f"Failed queries: {total_queries - successful_queries}")
    print(f"Cache hit rate: {cache_hits/total_queries*100:.1f}%")
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Average time per query: {total_time*1000/total_queries:.2f} ms")
    print(f"\n====MATCH SUMMARY====")
    print(f"Match success rate: {matches/total_queries*100:.1f}% ({matches})")
    print(f"Match miss rate: {misses/total_queries*100:.1f}% ({misses})")
    print(f"Top match: {top_1_match} ({top_1_match/matches*100:.1f}%)")
    print(f"Top 3 matches: {top_3_matches} ({top_3_matches/matches*100:.1f}%)")
    print(f"Top 5 matches: {top_5_matches} ({top_5_matches/matches*100:.1f}%)")
    print(f"Top 10 matches: {top_10_matches} ({top_10_matches/matches*100:.1f}%)")
    print(f"\n====MISSING TOOLS====")
    missing = [tool for result in results for tool in result.get('missing_tools', [])]
    if missing:
        count = Counter(missing)
        for name, value in count.items():
            print(f"{name}: {value}")



if __name__ == "__main__":
    # run_single_query()

    asyncio.run(test_run())