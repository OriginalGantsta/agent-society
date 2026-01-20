class Colors:
    USER = "\033[96m"
    ASSISTANT = "\033[92m"
    SYSTEM = "\033[90m"
    ERROR = "\033[91m"
    RESET = "\033[0m"

class CLIInterface:
    """Handles CLI input and output with formatting."""
    
    @staticmethod
    def print_system(message: str):
        print(f"{Colors.SYSTEM}{message}{Colors.RESET}")
        
    @staticmethod
    def print_error(message: str):
        print(f"{Colors.ERROR}{message}{Colors.RESET}")
        
    @staticmethod
    def print_user_prompt():
        print(f"\n{Colors.USER}You: {Colors.RESET}", end="")
        
    @staticmethod
    def get_input() -> str:
        return input()
        
    @staticmethod
    def print_assistant_prefix():
        print(f"{Colors.ASSISTANT}Assistant: {Colors.RESET}", end="", flush=True)
        
    @staticmethod
    def print_chunk(chunk_content: str):
        print(chunk_content, end="", flush=True)
        
    @staticmethod
    def print_separator():
        print(f"{Colors.SYSTEM}--------------------------------{Colors.RESET}")

