import json, http.client

class RequestHandler:
    def __init__(self):
        self.headers = {
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Authorization': f"Bearer None",
            'content-type': 'application/json'
        }       

    def route_request(self, query: str, url: str, top_k: int = 10) -> str:
        self.conn = http.client.HTTPConnection("localhost", 8000)
        payload = json.dumps({'query': query, 'top_k': top_k})

        try:
            self.conn.request("PUT", url, payload, self.headers)
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