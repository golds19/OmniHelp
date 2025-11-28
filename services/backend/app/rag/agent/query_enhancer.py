"""
Query expansion/enhancement utilities for improving retrieval.
"""

from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from ..core.config import HybridSearchConfig, LLMConfig


def enhance_query(query: str, llm: BaseChatModel, num_variations: int = None) -> List[str]:
    """
    Enhance a query by generating multiple alternative phrasings.

    Uses an LLM to generate semantically similar query variations that can
    improve retrieval recall by covering different ways of expressing the same intent.

    Args:
        query: The original query to enhance
        llm: The language model to use for generation
        num_variations: Number of variations to generate (default from config)

    Returns:
        List of query variations (including the original)

    Example:
        >>> enhance_query("main findings", llm)
        ["main findings", "key results", "primary discoveries", "important conclusions"]
    """
    if num_variations is None:
        num_variations = HybridSearchConfig.NUM_QUERY_VARIATIONS

    # Create prompt for query expansion
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a query expansion expert. Given a search query, generate {num_variations} alternative ways to phrase the same question.

Rules:
1. Keep the same intent and meaning
2. Use different words and phrasings
3. Make them suitable for document search
4. Return ONLY the alternative queries, one per line
5. Do NOT include explanations or numbering
6. Do NOT include the original query

Example:
Query: "main contributions"
Output:
key findings
primary results
novel contributions"""),
        ("user", "{query}")
    ])

    # Generate variations
    chain = prompt | llm
    response = chain.invoke({
        "query": query,
        "num_variations": num_variations
    })

    # Parse the response
    variations = [line.strip() for line in response.content.strip().split('\n') if line.strip()]

    # Return original + variations
    return [query] + variations[:num_variations]


def decompose_query(query: str, llm: BaseChatModel) -> List[str]:
    """
    Decompose a complex query into simpler sub-queries.

    Useful for multi-part questions that require breaking down into
    individual components for better retrieval.

    Args:
        query: The complex query to decompose
        llm: The language model to use for decomposition

    Returns:
        List of sub-queries

    Example:
        >>> decompose_query("Compare method A and B in terms of accuracy and speed", llm)
        ["What is the accuracy of method A?",
         "What is the accuracy of method B?",
         "What is the speed of method A?",
         "What is the speed of method B?"]
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a query decomposition expert. Given a complex query, break it down into simpler sub-queries.

Rules:
1. Each sub-query should be independent
2. Each sub-query should be answerable separately
3. Together, sub-queries should cover the original query
4. Return ONLY the sub-queries, one per line
5. Do NOT include explanations or numbering

Example:
Query: "Compare the performance of ResNet and VGG on ImageNet"
Output:
What is the performance of ResNet on ImageNet?
What is the performance of VGG on ImageNet?
How does ResNet compare to VGG?"""),
        ("user", "{query}")
    ])

    chain = prompt | llm
    response = chain.invoke({"query": query})

    # Parse the response
    sub_queries = [line.strip() for line in response.content.strip().split('\n') if line.strip()]

    return sub_queries


def generate_hypothetical_answer(query: str, llm: BaseChatModel) -> str:
    """
    Generate a hypothetical answer to the query (HyDE approach).

    This technique generates what an ideal answer might look like,
    then searches using that answer instead of the question.
    Often improves semantic matching.

    Args:
        query: The query to generate an answer for
        llm: The language model to use for generation

    Returns:
        Hypothetical answer text

    Example:
        >>> generate_hypothetical_answer("What is machine learning?", llm)
        "Machine learning is a subset of artificial intelligence that enables
        systems to learn and improve from experience without being explicitly
        programmed..."
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant. Generate a detailed, factual answer to the user's question.

Rules:
1. Write as if you're answering from a research paper or textbook
2. Be specific and technical
3. Include relevant terminology
4. Keep it 2-3 sentences
5. Do NOT say "I don't know" - generate a plausible answer"""),
        ("user", "{query}")
    ])

    chain = prompt | llm
    response = chain.invoke({"query": query})

    return response.content.strip()


if __name__ == "__main__":
    # Example usage
    from langchain_openai import ChatOpenAI

    # Use config for query enhancer model
    llm = ChatOpenAI(model=LLMConfig.QUERY_ENHANCER_MODEL, temperature=LLMConfig.QUERY_ENHANCER_TEMPERATURE)

    # Test query expansion
    original = "main contributions"
    expanded = enhance_query(original, llm, num_variations=3)
    print("Query Expansion:")
    print(f"Original: {original}")
    print(f"Expanded: {expanded}")

    # Test query decomposition
    complex_query = "Compare ResNet and VGG on ImageNet"
    sub_queries = decompose_query(complex_query, llm)
    print("\nQuery Decomposition:")
    print(f"Original: {complex_query}")
    print(f"Sub-queries: {sub_queries}")

    # Test HyDE
    question = "What is transfer learning?"
    hypo_answer = generate_hypothetical_answer(question, llm)
    print("\nHyDE:")
    print(f"Question: {question}")
    print(f"Hypothetical Answer: {hypo_answer}")
