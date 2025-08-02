"""
Query Parser Module

Handles parsing and structuring of natural language queries to extract
relevant information like age, gender, procedure, location, etc.
"""

import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

import openai
from loguru import logger

import config


class Gender(Enum):
    """Enum for gender values."""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"


@dataclass
class ParsedQuery:
    """Structured representation of a parsed query."""
    original_query: str
    age: Optional[int] = None
    gender: Optional[Gender] = None
    procedure: Optional[str] = None
    location: Optional[str] = None
    policy_duration: Optional[str] = None
    medical_condition: Optional[str] = None
    amount_claimed: Optional[str] = None
    date_of_service: Optional[str] = None
    additional_info: Dict[str, Any] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "original_query": self.original_query,
            "age": self.age,
            "gender": self.gender.value if self.gender else None,
            "procedure": self.procedure,
            "location": self.location,
            "policy_duration": self.policy_duration,
            "medical_condition": self.medical_condition,
            "amount_claimed": self.amount_claimed,
            "date_of_service": self.date_of_service,
            "additional_info": self.additional_info,
            "confidence": self.confidence
        }


class QueryParser:
    """Parses natural language queries into structured data."""
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize the query parser.
        
        Args:
            use_llm: Whether to use LLM for advanced parsing
        """
        self.use_llm = use_llm
        
        # Regex patterns for common extractions
        self.patterns = {
            "age": [
                r"(\d{1,3})\s*(?:years?\s*old|y\.?o\.?|M|F)",
                r"age\s*:?\s*(\d{1,3})",
                r"(\d{1,3})\s*(?:male|female|M|F)"
            ],
            "gender": [
                r"\b(male|female|M|F|man|woman)\b",
                r"(\d+)\s*(M|F)\b"
            ],
            "amount": [
                r"₹\s*(\d+(?:,\d+)*(?:\.\d+)?)",
                r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rupees?|INR|Rs\.?)",
                r"claim\s*(?:of|for)?\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)"
            ],
            "duration": [
                r"(\d+)\s*(?:month|year)s?\s*(?:policy|coverage|term)",
                r"(?:policy|coverage|term)\s*(?:of|for)?\s*(\d+)\s*(?:month|year)s?"
            ]
        }
        
        # Medical procedure keywords
        self.medical_keywords = {
            "surgery": ["surgery", "operation", "procedure", "surgical"],
            "treatment": ["treatment", "therapy", "medication", "medicine"],
            "diagnosis": ["diagnosis", "condition", "disease", "illness"],
            "emergency": ["emergency", "urgent", "critical", "accident"]
        }
        
        # Indian cities for location detection
        self.indian_cities = {
            "mumbai", "delhi", "bangalore", "hyderabad", "chennai", "kolkata",
            "pune", "ahmedabad", "surat", "jaipur", "lucknow", "kanpur",
            "nagpur", "indore", "thane", "bhopal", "visakhapatnam", "pimpri"
        }
        
        logger.info(f"Initialized QueryParser with LLM support: {use_llm}")
    
    def extract_age(self, text: str) -> Optional[int]:
        """
        Extract age from text using regex patterns.
        
        Args:
            text: Input text
            
        Returns:
            Extracted age or None
        """
        for pattern in self.patterns["age"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 0 <= age <= 120:  # Reasonable age range
                    return age
        return None
    
    def extract_gender(self, text: str) -> Optional[Gender]:
        """
        Extract gender from text using regex patterns.
        
        Args:
            text: Input text
            
        Returns:
            Extracted gender or None
        """
        for pattern in self.patterns["gender"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender_text = match.group(1).lower()
                if gender_text in ["male", "m", "man"]:
                    return Gender.MALE
                elif gender_text in ["female", "f", "woman"]:
                    return Gender.FEMALE
        return None
    
    def extract_amount(self, text: str) -> Optional[str]:
        """
        Extract monetary amount from text.
        
        Args:
            text: Input text
            
        Returns:
            Extracted amount as string or None
        """
        for pattern in self.patterns["amount"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_duration(self, text: str) -> Optional[str]:
        """
        Extract policy duration from text.
        
        Args:
            text: Input text
            
        Returns:
            Extracted duration or None
        """
        for pattern in self.patterns["duration"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                duration = match.group(1)
                # Determine if it's months or years from context
                if "month" in text.lower():
                    return f"{duration} months"
                elif "year" in text.lower():
                    return f"{duration} years"
                else:
                    return f"{duration} months"  # Default to months
        return None
    
    def extract_procedure(self, text: str) -> Optional[str]:
        """
        Extract medical procedure from text.
        
        Args:
            text: Input text
            
        Returns:
            Extracted procedure or None
        """
        text_lower = text.lower()
        
        # Look for specific procedures
        procedures = [
            "knee surgery", "hip surgery", "heart surgery", "brain surgery",
            "appendectomy", "gallbladder surgery", "cataract surgery",
            "bypass surgery", "angioplasty", "chemotherapy", "dialysis"
        ]
        
        for procedure in procedures:
            if procedure in text_lower:
                return procedure
        
        # Look for general medical keywords
        for category, keywords in self.medical_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Try to extract context around the keyword
                    pattern = rf"\b\w+\s+{keyword}\b|\b{keyword}\s+\w+\b"
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(0).strip()
        
        return None
    
    def extract_location(self, text: str) -> Optional[str]:
        """
        Extract location from text.
        
        Args:
            text: Input text
            
        Returns:
            Extracted location or None
        """
        text_lower = text.lower()
        
        for city in self.indian_cities:
            if city in text_lower:
                return city.title()
        
        return None
    
    def parse_with_regex(self, query: str) -> ParsedQuery:
        """
        Parse query using regex patterns.
        
        Args:
            query: Natural language query
            
        Returns:
            ParsedQuery object with extracted information
        """
        parsed = ParsedQuery(original_query=query)
        
        parsed.age = self.extract_age(query)
        parsed.gender = self.extract_gender(query)
        parsed.amount_claimed = self.extract_amount(query)
        parsed.policy_duration = self.extract_duration(query)
        parsed.procedure = self.extract_procedure(query)
        parsed.location = self.extract_location(query)
        
        # Calculate confidence based on how much information was extracted
        fields_found = sum(1 for field in [
            parsed.age, parsed.gender, parsed.procedure, 
            parsed.location, parsed.policy_duration
        ] if field is not None)
        parsed.confidence = fields_found / 5.0  # 5 main fields
        
        return parsed
    
    def parse_with_llm(self, query: str) -> ParsedQuery:
        """
        Parse query using LLM for more advanced understanding.
        
        Args:
            query: Natural language query
            
        Returns:
            ParsedQuery object with extracted information
        """
        if not config.OPENAI_API_KEY:
            logger.warning("OpenAI API key not available, falling back to regex parsing")
            return self.parse_with_regex(query)
        
        prompt = f"""
        Extract structured information from the following insurance/medical query.
        Return a JSON object with the following fields (use null for missing information):
        
        - age: integer (person's age)
        - gender: string ("Male", "Female", "Other", or "Unknown")
        - procedure: string (medical procedure or treatment)
        - location: string (city or location)
        - policy_duration: string (e.g., "3 months", "1 year")
        - medical_condition: string (any medical condition mentioned)
        - amount_claimed: string (any monetary amount)
        - date_of_service: string (any date mentioned)
        
        Query: "{query}"
        
        Respond only with valid JSON:
        """
        
        try:
            response = openai.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from insurance and medical queries. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Create ParsedQuery object from LLM result
            parsed = ParsedQuery(original_query=query)
            parsed.age = result.get("age")
            
            # Convert gender string to enum
            gender_str = result.get("gender")
            if gender_str:
                try:
                    parsed.gender = Gender(gender_str)
                except ValueError:
                    parsed.gender = Gender.UNKNOWN
            
            parsed.procedure = result.get("procedure")
            parsed.location = result.get("location")
            parsed.policy_duration = result.get("policy_duration")
            parsed.medical_condition = result.get("medical_condition")
            parsed.amount_claimed = result.get("amount_claimed")
            parsed.date_of_service = result.get("date_of_service")
            
            # Calculate confidence based on LLM extraction
            fields_found = sum(1 for value in result.values() if value is not None)
            parsed.confidence = min(fields_found / 8.0, 1.0)  # 8 total fields
            
            logger.info(f"LLM parsing completed with confidence: {parsed.confidence}")
            return parsed
            
        except Exception as e:
            logger.error(f"Error in LLM parsing: {e}")
            return self.parse_with_regex(query)
    
    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query into structured data.
        
        Args:
            query: Natural language query
            
        Returns:
            ParsedQuery object with extracted information
        """
        if self.use_llm:
            return self.parse_with_llm(query)
        else:
            return self.parse_with_regex(query)
    
    def enhance_query(self, parsed_query: ParsedQuery) -> str:
        """
        Create an enhanced query string for better retrieval.
        
        Args:
            parsed_query: ParsedQuery object
            
        Returns:
            Enhanced query string
        """
        components = []
        
        if parsed_query.age:
            components.append(f"age {parsed_query.age}")
        
        if parsed_query.gender:
            components.append(parsed_query.gender.value.lower())
        
        if parsed_query.procedure:
            components.append(parsed_query.procedure)
        
        if parsed_query.medical_condition:
            components.append(parsed_query.medical_condition)
        
        if parsed_query.location:
            components.append(parsed_query.location)
        
        if parsed_query.policy_duration:
            components.append(parsed_query.policy_duration)
        
        # Add original query terms that weren't captured
        original_words = set(parsed_query.original_query.lower().split())
        component_words = set(" ".join(components).lower().split())
        additional_words = original_words - component_words
        
        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        additional_words = additional_words - stop_words
        
        components.extend(additional_words)
        
        enhanced_query = " ".join(components)
        logger.info(f"Enhanced query: {enhanced_query}")
        
        return enhanced_query


# Example usage
if __name__ == "__main__":
    parser = QueryParser(use_llm=False)  # Use regex for demo
    
    # Test queries
    test_queries = [
        "46M, knee surgery, Pune, 3-month policy",
        "Female patient, 35 years old, heart surgery in Mumbai, claim amount ₹2,50,000",
        "Appendectomy for 28-year-old male in Delhi, 1-year policy coverage"
    ]
    
    for query in test_queries:
        parsed = parser.parse(query)
        print(f"\nQuery: {query}")
        print(f"Parsed: {parsed.to_dict()}")
        print(f"Enhanced: {parser.enhance_query(parsed)}")
