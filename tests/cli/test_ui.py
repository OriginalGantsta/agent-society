from agent.cli.ui import CLIInterface, Colors

def test_given_message_when_print_system_called_then_prints_formatted(capsys):
    message = "System message"
    CLIInterface.print_system(message)
    
    captured = capsys.readouterr()
    expected_output = f"{Colors.SYSTEM}{message}{Colors.RESET}\n"
    assert captured.out == expected_output

def test_given_input_when_get_input_called_then_returns_string(monkeypatch):
    expected_input = "user input"
    monkeypatch.setattr('builtins.input', lambda: expected_input)
    
    result = CLIInterface.get_input()
    assert result == expected_input

