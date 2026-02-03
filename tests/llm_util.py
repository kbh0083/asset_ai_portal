from langchain_core.callbacks import BaseCallbackHandler

class StreamPrinter(BaseCallbackHandler):
    """LLM이 토큰을 생성할 때마다 콘솔에 출력"""
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self._printed_prefix = False

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if not self._printed_prefix and self.prefix:
            print(f"\n[{self.prefix}] ", end="", flush=True)
            self._printed_prefix = True
        print(token, end="", flush=True)

    def on_llm_end(self, response, **kwargs) -> None:
        print("\n", flush=True)
        self._printed_prefix = False
