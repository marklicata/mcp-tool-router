import json, http.client, asyncio
from utils import TestRunManager

def run_chat():
  headers = {
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Authorization': f"Bearer None",
      'content-type': 'application/json'
    }

  # query = input("Type a query to route to tools (or press Enter to exit)... ")
  query = "How do I clone a repo in GitHub?"
  while query is not None and query != "":
    payload = json.dumps({'query': query})

    try:
      conn = http.client.HTTPConnection("localhost", 8000)
      conn.request("PUT", f"/get_mcp_tools/", body=payload, headers=headers)
      res = conn.getresponse()
      data = res.read()
      parsed_json = json.loads(data.decode("utf-8"))
      formatted_json = json.dumps(parsed_json, indent=4)
      print(formatted_json)
    except Exception as e:
        print(f"Error occurred: {e}")

    query = input("Type a new query or press Enter to exit... ")
  conn.close()



if __name__ == "__main__":
    # run_chat()

    test_runner = TestRunManager()
    asyncio.run(test_runner.run_multiple_test_cases())

    # with open("python/src/app/data/test_results.json", "r") as f:
    #     results = json.load(f)


    # tools_cnt = 0
    # test_cases_cnt = 0
    # missed_tools = {}
    # for result in results:
    #     missing_tool = result.get("missing_tools", [])
    #     if missing_tool is not None and len(missing_tool) > 0:
    #         test_cases_cnt += 1
    #         tools_cnt += len(missing_tool)
    #         for tool in missing_tool:
    #             if tool not in missed_tools:
    #                 missed_tools[tool] = 1
    #             else:
    #                 missed_tools[tool] += 1
    # print(f"average missing tools per test case: {tools_cnt / test_cases_cnt if test_cases_cnt > 0 else 0}")
    # print(json.dumps(missed_tools, indent=4))
