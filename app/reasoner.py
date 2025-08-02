"""
LLM Reasoning Module

Uses Large Language Models to analyze retrieved document chunks and make
intelligent decisions about insurance claims, policy coverage, and eligibility.
"""

import json
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

import openai
from loguru import logger

import config
from app.ingestion import DocumentChunk
from app.parser import ParsedQuery


class Decision(Enum):
    """Enum for decision types."""
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PENDING = "Pending"
    INSUFFICIENT_INFO = "Insufficient Information"


@dataclass
class ClauseReference:
    """Reference to a specific policy clause."""
    text: str
    source: str
    relevance_score: float
    section: Optional[str] = None


@dataclass
class ReasoningResult:
    """Result of LLM reasoning process."""
    decision: Decision
    amount: Optional[str] = None
    confidence: float = 0.0
    justification: List[ClauseReference] = None
    reasoning: str = ""
    recommendations: List[str] = None
    query_understanding: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.justification is None:
            self.justification = []
        if self.recommendations is None:
            self.recommendations = []
        if self.query_understanding is None:
            self.query_understanding = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "decision": self.decision.value,
            "amount": self.amount,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "justification": {
                "clauses": [
                    {
                        "text": clause.text,
                        "source": clause.source,
                        "section": clause.section,
                        "relevance_score": clause.relevance_score
                    }
                    for clause in self.justification
                ]
            },
            "recommendations": self.recommendations,
            "query_understanding": self.query_understanding
        }


class LLMReasoner:
    """Handles LLM-based reasoning and decision making."""
    
    def __init__(self, model_name: str = config.OPENAI_MODEL):
        """
        Initialize the LLM reasoner.
        
        Args:
            model_name: Name of the OpenAI model to use
        """
        self.model_name = model_name
        
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found in environment variables")
        
        openai.api_key = config.OPENAI_API_KEY
        logger.info(f"Initialized LLMReasoner with model: {model_name}")
    
    def create_decision_prompt(
        self, 
        parsed_query: ParsedQuery, 
        context: str,
        retrieved_chunks: List[Tuple[DocumentChunk, float]]
    ) -> str:
        """
        Create a prompt for the LLM to make decisions.
        
        Args:
            parsed_query: Parsed query information
            context: Retrieved document context
            retrieved_chunks: List of relevant document chunks
            
        Returns:
            Formatted prompt string
        """
        # Format query information
        query_info = f"""
QUERY INFORMATION:
Original Query: {parsed_query.original_query}
Age: {parsed_query.age or 'Not specified'}
Gender: {parsed_query.gender.value if parsed_query.gender else 'Not specified'}
Procedure: {parsed_query.procedure or 'Not specified'}
Medical Condition: {parsed_query.medical_condition or 'Not specified'}
Location: {parsed_query.location or 'Not specified'}
Policy Duration: {parsed_query.policy_duration or 'Not specified'}
Amount Claimed: {parsed_query.amount_claimed or 'Not specified'}
Date of Service: {parsed_query.date_of_service or 'Not specified'}
"""
        
        # Format context
        context_section = f"""
RELEVANT POLICY DOCUMENTS:
{context}
"""
        
        # Create the main prompt
        prompt = f"""
You are an expert insurance claim analyst. Analyze the following query and policy documents to make a decision about claim eligibility.

{query_info}

{context_section}

TASK:
Based on the query and policy documents, determine:
1. Whether the claim should be APPROVED, REJECTED, PENDING, or marked as INSUFFICIENT_INFO
2. If approved, the coverage amount (if determinable)
3. Specific policy clauses that support your decision
4. Clear reasoning for your decision
5. Any recommendations or additional requirements

RESPONSE FORMAT:
Respond with a JSON object containing:
{{
    "decision": "APPROVED/REJECTED/PENDING/INSUFFICIENT_INFO",
    "amount": "Amount if determinable (e.g., '₹1,50,000') or null",
    "confidence": 0.0-1.0,
    "reasoning": "Clear explanation of your decision",
    "supporting_clauses": [
        {{
            "text": "Exact text from policy document",
            "source": "Document name and section",
            "relevance": "How this clause applies to the case"
        }}
    ],
    "recommendations": ["List of any recommendations or requirements"]
}}

GUIDELINES:
- Be thorough but concise in your reasoning
- Quote exact text from policy documents when possible
- Consider age, gender, procedure type, location, and policy duration
- If information is missing, indicate what additional information is needed
- Be fair and objective in your analysis
- Consider both inclusions and exclusions in the policy

Respond only with valid JSON:
"""
        
        return prompt
    
    def analyze_claim(
        self, 
        parsed_query: ParsedQuery,
        retrieved_chunks: List[Tuple[DocumentChunk, float]],
        context: str
    ) -> ReasoningResult:
        """
        Analyze a claim using LLM reasoning.
        
        Args:
            parsed_query: Parsed query information
            retrieved_chunks: List of relevant document chunks
            context: Formatted context from retrieved chunks
            
        Returns:
            ReasoningResult object
        """
        try:
            # Create the prompt
            prompt = self.create_decision_prompt(parsed_query, context, retrieved_chunks)
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert insurance claim analyst with deep knowledge of policy terms, medical procedures, and claim processing. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent reasoning
                max_tokens=1500
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            logger.info(f"LLM response received: {len(response_text)} characters")
            
            # Parse JSON response
            result_data = json.loads(response_text)
            
            # Create ReasoningResult object
            result = ReasoningResult(
                decision=Decision(result_data["decision"]),
                amount=result_data.get("amount"),
                confidence=result_data.get("confidence", 0.0),
                reasoning=result_data.get("reasoning", ""),
                recommendations=result_data.get("recommendations", []),
                query_understanding=parsed_query.to_dict()
            )
            
            # Process supporting clauses
            for clause_data in result_data.get("supporting_clauses", []):
                # Find the source chunk for relevance score
                relevance_score = 0.0
                for chunk, score in retrieved_chunks:
                    if clause_data["source"].lower() in chunk.source.lower():
                        relevance_score = score
                        break
                
                clause = ClauseReference(
                    text=clause_data["text"],
                    source=clause_data["source"],
                    relevance_score=relevance_score,
                    section=clause_data.get("section")
                )
                result.justification.append(clause)
            
            logger.info(f"Analysis completed: {result.decision.value} with confidence {result.confidence}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return self._create_error_result(parsed_query, "Failed to parse LLM response")
        
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return self._create_error_result(parsed_query, str(e))
    
    def _create_error_result(self, parsed_query: ParsedQuery, error_message: str) -> ReasoningResult:
        """
        Create an error result when LLM analysis fails.
        
        Args:
            parsed_query: Original parsed query
            error_message: Error message
            
        Returns:
            ReasoningResult with error information
        """
        return ReasoningResult(
            decision=Decision.INSUFFICIENT_INFO,
            confidence=0.0,
            reasoning=f"Unable to process request: {error_message}",
            recommendations=["Please try again or contact support"],
            query_understanding=parsed_query.to_dict()
        )
    
    def explain_decision(self, result: ReasoningResult) -> str:
        """
        Generate a human-readable explanation of the decision.
        
        Args:
            result: ReasoningResult object
            
        Returns:
            Formatted explanation string
        """
        explanation = f"""
DECISION: {result.decision.value}
CONFIDENCE: {result.confidence:.1%}
"""
        
        if result.amount:
            explanation += f"AMOUNT: {result.amount}\n"
        
        explanation += f"\nREASONING:\n{result.reasoning}\n"
        
        if result.justification:
            explanation += "\nSUPPORTING EVIDENCE:\n"
            for i, clause in enumerate(result.justification, 1):
                explanation += f"{i}. {clause.text}\n   Source: {clause.source}\n\n"
        
        if result.recommendations:
            explanation += "RECOMMENDATIONS:\n"
            for i, rec in enumerate(result.recommendations, 1):
                explanation += f"{i}. {rec}\n"
        
        return explanation
    
    def validate_decision(self, result: ReasoningResult) -> Dict[str, Any]:
        """
        Validate the reasoning result for consistency and completeness.
        
        Args:
            result: ReasoningResult object
            
        Returns:
            Validation report
        """
        validation = {
            "is_valid": True,
            "issues": [],
            "score": 1.0
        }
        
        # Check if decision has supporting evidence
        if result.decision in [Decision.APPROVED, Decision.REJECTED] and not result.justification:
            validation["issues"].append("Decision lacks supporting clauses")
            validation["score"] -= 0.3
        
        # Check confidence level
        if result.confidence < 0.5:
            validation["issues"].append("Low confidence in decision")
            validation["score"] -= 0.2
        
        # Check reasoning quality
        if len(result.reasoning) < 50:
            validation["issues"].append("Reasoning is too brief")
            validation["score"] -= 0.2
        
        # Check for amount when approved
        if result.decision == Decision.APPROVED and not result.amount:
            validation["issues"].append("Approved claim missing amount")
            validation["score"] -= 0.2
        
        validation["is_valid"] = validation["score"] >= 0.5
        
        return validation


class PolicyAnalyzer:
    """Specialized analyzer for policy-specific operations."""
    
    def __init__(self, llm_reasoner: LLMReasoner):
        """
        Initialize policy analyzer.
        
        Args:
            llm_reasoner: LLMReasoner instance
        """
        self.llm_reasoner = llm_reasoner
    
    def extract_coverage_limits(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Extract coverage limits and exclusions from policy documents.
        
        Args:
            chunks: Policy document chunks
            
        Returns:
            Dictionary with coverage information
        """
        # This would use LLM to extract structured policy information
        # For now, return a placeholder
        return {
            "max_coverage": "₹5,00,000",
            "deductible": "₹10,000",
            "exclusions": ["Pre-existing conditions", "Cosmetic surgery"],
            "waiting_period": "30 days"
        }
    
    def check_eligibility_criteria(self, parsed_query: ParsedQuery) -> Dict[str, bool]:
        """
        Check basic eligibility criteria.
        
        Args:
            parsed_query: Parsed query information
            
        Returns:
            Dictionary with eligibility checks
        """
        eligibility = {
            "age_eligible": True,
            "procedure_covered": True,
            "location_covered": True,
            "policy_active": True
        }
        
        # Basic age check
        if parsed_query.age and (parsed_query.age < 18 or parsed_query.age > 65):
            eligibility["age_eligible"] = False
        
        return eligibility


# Example usage
if __name__ == "__main__":
    from app.parser import QueryParser
    from app.retriever import SemanticRetriever
    from app.embedder import EmbeddingGenerator
    
    # Initialize components (mock for demo)
    parser = QueryParser(use_llm=False)
    reasoner = LLMReasoner()
    
    # Test query
    test_query = "46M, knee surgery, Pune, 3-month policy, claim ₹1,50,000"
    parsed_query = parser.parse(test_query)
    
    # Mock retrieved chunks and context
    mock_context = """
    Section 2.1: Surgical Procedures
    Knee surgery is covered for policyholders aged 18-60.
    Maximum coverage: ₹2,00,000 per procedure.
    Location: Coverage available in all metro cities including Pune.
    """
    
    print(f"Query: {test_query}")
    print(f"Parsed: {parsed_query.to_dict()}")
    
    # Note: Actual analysis would require valid API key and context
    print("\nReady for LLM analysis (requires OpenAI API key)")
