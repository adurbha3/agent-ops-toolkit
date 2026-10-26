from agentops.routing import route, ToolChoice


def test_routes_plain_arithmetic_phrase_to_calculate():
    assert route("What is 800 times 1.2?") == ToolChoice.CALCULATE


def test_routes_phrase_with_filler_words_to_calculate():
    assert route("What is the base rate 600 multiplied by 1.3?") == ToolChoice.CALCULATE


def test_routes_document_question_to_search():
    assert route("What does collision coverage pay for?") == ToolChoice.SEARCH
    assert route("How does a deductible work?") == ToolChoice.SEARCH


def test_number_without_math_keyword_routes_to_search():
    # Mentions a number but isn't asking for a calculation.
    assert route("What is the deductible on a 2019 policy?") == ToolChoice.SEARCH


def test_math_keyword_without_number_routes_to_search():
    assert route("What does times mean in an insurance context?") == ToolChoice.SEARCH
