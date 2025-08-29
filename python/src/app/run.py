import json, http.client, asyncio
from utils_test_manager import TestRunManager

def run_chat():
  headers = {
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Authorization': f"Bearer None",
      'content-type': 'application/json'
    }

  # query = input("Type a query to route to tools (or press Enter to exit)... ")
  query = "How do I clone a repo in GitHub?"
  allowed_tools = []

  while query is not None and query != "":
    payload = json.dumps({
       'query': query,
       'allowed_tools': allowed_tools
    })

    try:
      conn = http.client.HTTPConnection("localhost", 8000)
      conn.request("PUT", f"/get_mcp_tools/", body=payload, headers=headers)
      res = conn.getresponse()
      data = res.read()
      parsed_json = json.loads(data.decode("utf-8"))
      formatted_json = json.dumps(parsed_json, indent=4)
    except Exception as e:
        print(f"Error occurred: {e}")

    query = input("Type a new query or press Enter to exit... ")
  conn.close()



if __name__ == "__main__":
    # run_chat()

    test_runner = TestRunManager()
    asyncio.run(test_runner.run_multiple_test_cases())
    
