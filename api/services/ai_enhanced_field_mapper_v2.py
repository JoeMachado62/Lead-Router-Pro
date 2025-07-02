# api/services/ai_enhanced_field_mapper_v2.py
# V2 Enhanced field mapper using the standalone FieldReferenceService

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import the base field mapper (your existing one)
from .field_mapper import FieldMapper
# Import V2 services
from .field_reference_service import field_reference_service
from .ai_error_recovery_v2 import ai_error_recovery_v2

logger = logging.getLogger(__name__)

class AIEnhancedFieldMapperV2(FieldMapper):
    """
    V2 Enhanced field mapper with AI-powered field analysis
    
    Key V2 improvements:
    - Uses standalone FieldReferenceService (no duplication)
    - Leverages V2 AI error recovery caching
    - Better separation of concerns
    - Production monitoring and metrics
    """
    
    def __init__(self):
        super().__init__()
        
        # Use the shared field reference service instead of loading our own
        self.field_reference_service = field_reference_service
        self.ai_enabled = ai_error_recovery_v2.enabled
        self.anthropic_client = ai_error_recovery_v2.client if self.ai_enabled else None
        
        # V2 metrics
        self.analysis_count = 0
        self.auto_saved_mappings = 0
        self.cache_hits = 0
        
        logger.info(f"🤖 AI Enhanced Field Mapper V2 initialized")
        logger.info(f"   🧠 AI Analysis: {'✅ Enabled' if self.ai_enabled else '❌ Disabled'}")
        logger.info(f"   🗂️ Field Reference: {len(self.field_reference_service.field_reference)} fields loaded")
    
    async def analyze_unknown_field_with_ai(self, 
                                           field_name: str, 
                                           field_value: Any, 
                                           context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        V2 AI field analysis using shared services and caching
        
        Args:
            field_name: The unknown field name from the form
            field_value: The value of the field
            context: Additional context (form data, form type, etc.)
        
        Returns:
            AI analysis with mapping suggestions
        """
        
        self.analysis_count += 1
        
        if not self.ai_enabled:
            return self._fallback_field_analysis_v2(field_name, field_value, context)
        
        try:
            # First, check if we have similar fields via the reference service
            similar_fields = self.field_reference_service.find_similar_fields(field_name)
            
            # If we have high-confidence matches, return immediately (cache-like behavior)
            if similar_fields and similar_fields[0][2] > 0.8:
                self.cache_hits += 1
                best_match = similar_fields[0]
                logger.info(f"🎯 High-confidence field match found: {field_name} → {best_match[0]} (score: {best_match[2]:.2f})")
                
                return {
                    "success": True,
                    "ai_powered": False,  # Rule-based high-confidence match
                    "field_purpose": f"High-confidence match for {field_name}",
                    "recommended_mapping": {
                        "ghl_field_key": best_match[0],
                        "ghl_field_name": best_match[1].get('name', ''),
                        "confidence": "high"
                    },
                    "reasoning": f"Strong similarity match (score: {best_match[2]:.2f})",
                    "similarity_score": best_match[2],
                    "cache_hit": True
                }
            
            # If no high-confidence match, use AI analysis
            analysis_context = self._prepare_field_analysis_context_v2(field_name, field_value, context)
            prompt = self._build_field_analysis_prompt_v2(analysis_context)
            
            # Use the same AI client as error recovery for consistency
            response = await self._query_claude_for_field_analysis_v2(prompt)
            
            if response and response.get("success"):
                analysis = self._parse_field_analysis_response_v2(response["content"])
                logger.info(f"🤖 AI field analysis for '{field_name}': {analysis.get('confidence', 'unknown')} confidence")
                return analysis
            else:
                logger.warning(f"🤖 AI field analysis failed for '{field_name}', using V2 fallback")
                return self._fallback_field_analysis_v2(field_name, field_value, context)
                
        except Exception as e:
            logger.error(f"❌ AI field analysis exception for '{field_name}': {e}")
            return self._fallback_field_analysis_v2(field_name, field_value, context)
    
    def _prepare_field_analysis_context_v2(self, 
                                          field_name: str, 
                                          field_value: Any, 
                                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """V2 context preparation using shared field reference service"""
        
        # Get only relevant fields from the shared service (token-efficient)
        payload_keys = [field_name]
        if context and context.get('form_data'):
            payload_keys.extend(context['form_data'].keys())
        
        relevant_fields = self.field_reference_service.slice_relevant_fields(
            payload_keys=payload_keys,
            error_text="",
            max_fields=10  # Limit for token efficiency
        )
        
        # Analyze field value characteristics
        value_analysis = self._analyze_field_value_v2(field_value)
        
        return {
            "field_details": {
                "name": field_name,
                "value": str(field_value)[:100] if field_value else "",
                "value_type": type(field_value).__name__,
                "value_analysis": value_analysis
            },
            "form_context": context or {},
            "relevant_ghl_fields": relevant_fields,
            "similar_fields": self.field_reference_service.find_similar_fields(field_name, max_results=3),
            "industry": "marine",
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_field_value_v2(self, value: Any) -> Dict[str, Any]:
        """Enhanced field value analysis for V2"""
        
        if value is None:
            return {"type": "null", "characteristics": []}
        
        value_str = str(value).strip()
        characteristics = []
        likely_types = []
        
        # Email detection
        if "@" in value_str and "." in value_str:
            characteristics.append("contains_email_pattern")
            likely_types.append("email")
        
        # Phone detection  
        if any(c.isdigit() for c in value_str) and len([c for c in value_str if c.isdigit()]) >= 10:
            characteristics.append("contains_phone_pattern")
            likely_types.append("phone")
        
        # ZIP code detection
        if value_str.isdigit() and len(value_str) == 5:
            characteristics.append("five_digit_number")
            likely_types.append("zip_code")
        
        # Marine-specific patterns
        marine_terms = ["boat", "yacht", "vessel", "engine", "sail", "motor", "dock", "marina"]
        if any(term in value_str.lower() for term in marine_terms):
            characteristics.append("marine_related")
            likely_types.append("marine_field")
        
        # Service-related patterns  
        service_terms = ["service", "repair", "maintenance", "cleaning", "installation"]
        if any(term in value_str.lower() for term in service_terms):
            characteristics.append("service_related")
            likely_types.append("service_field")
        
        return {
            "type": type(value).__name__,
            "length": len(value_str),
            "characteristics": characteristics,
            "likely_types": likely_types,
            "is_empty": not value_str,
            "sample": value_str[:50],
            "marine_context": "marine_related" in characteristics
        }
    
    def _build_field_analysis_prompt_v2(self, context: Dict[str, Any]) -> str:
        """V2 prompt building with token optimization"""
        
        field_name = context["field_details"]["name"]
        field_value = context["field_details"]["value"]
        value_analysis = context["field_details"]["value_analysis"]
        relevant_fields = context["relevant_ghl_fields"]
        similar_fields = context["similar_fields"]
        
        # Compact field summaries for token efficiency
        field_summaries = []
        for key, field_def in list(relevant_fields.items())[:8]:  # Limit for tokens
            field_summaries.append(f"{key}:{field_def.get('dataType', 'TEXT')}")
        
        # Include top similar fields
        similarity_info = ""
        if similar_fields:
            top_similar = similar_fields[0]
            similarity_info = f"Most similar existing field: {top_similar[0]} (score: {top_similar[2]:.2f})"
        
        return f"""You are an expert at mapping marine service form fields to GoHighLevel custom fields.

FIELD TO ANALYZE:
Name: "{field_name}"
Value: "{field_value}"
Type: {value_analysis.get('type', 'unknown')}
Characteristics: {value_analysis.get('characteristics', [])}
Marine Context: {value_analysis.get('marine_context', False)}

AVAILABLE GHL FIELDS:
{', '.join(field_summaries)}

{similarity_info}

MARINE SERVICE CONTEXT:
- Common fields: vessel_make, vessel_model, vessel_year, vessel_length_ft, zip_code_of_service
- Service types: Boat Maintenance, Marine Systems, Engines and Generators
- Industry: Marine services (boat repairs, yacht maintenance, dock services)

TASK: Analyze this field and suggest the best GHL mapping. Consider:
1. Field name similarity to existing GHL fields
2. Value characteristics and data type compatibility  
3. Marine industry context and common patterns
4. Whether to map to existing field or create new one

Respond with a JSON object containing your analysis and recommendations."""
    
    async def _query_claude_for_field_analysis_v2(self, prompt: str) -> Dict[str, Any]:
        """V2 Claude querying using shared AI service settings"""
        
        try:
            # Use the same client and settings as error recovery for consistency
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,  # Reduced for efficiency
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text if response.content else ""
            
            return {
                "success": True,
                "content": content,
                "usage": {
                    "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                    "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Claude field analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_field_analysis_response_v2(self, content: str) -> Dict[str, Any]:
        """V2 response parsing with better error handling"""
        
        try:
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                analysis = json.loads(json_content)
                
                # Validate and normalize the response
                return {
                    "success": True,
                    "ai_powered": True,
                    "field_purpose": analysis.get("field_purpose", "AI-analyzed field"),
                    "recommended_mapping": {
                        "ghl_field_key": analysis.get("ghl_field_key", "unknown"),
                        "ghl_field_name": analysis.get("ghl_field_name", "Unknown Field"),
                        "confidence": analysis.get("confidence", "medium")
                    },
                    "reasoning": analysis.get("reasoning", "AI analysis completed"),
                    "create_new_field": analysis.get("create_new_field", False),
                    "alternative_mappings": analysis.get("alternative_mappings", [])
                }
            
            # Fallback parsing
            logger.warning("⚠️ Could not parse complete Claude field analysis response")
            return {
                "success": False,
                "ai_powered": True,
                "field_purpose": "Unknown - parsing failed",
                "recommended_mapping": {
                    "ghl_field_key": "special_requests__notes",
                    "ghl_field_name": "Special Requests / Notes",
                    "confidence": "low"
                },
                "reasoning": "Could not parse AI response",
                "raw_response": content[:300]
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error in field analysis: {e}")
            return self._create_fallback_analysis("JSON parsing failed", content[:300])
    
    def _fallback_field_analysis_v2(self, 
                                   field_name: str, 
                                   field_value: Any, 
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """V2 fallback using field reference service for better accuracy"""
        
        # Use the field reference service for suggestions
        suggestions = self.field_reference_service.get_field_suggestions(field_name, context)
        
        if suggestions["similar_fields"]:
            best_suggestion = suggestions["similar_fields"][0]
            confidence = best_suggestion["confidence"]
            
            return {
                "success": True,
                "ai_powered": False,
                "field_purpose": suggestions["field_analysis"]["likely_type"].title() + " field",
                "recommended_mapping": {
                    "ghl_field_key": best_suggestion["field_key"],
                    "ghl_field_name": best_suggestion["field_name"],
                    "confidence": confidence
                },
                "reasoning": f"Field reference service suggestion (similarity: {best_suggestion['similarity_score']:.2f})",
                "recommendations": suggestions["recommendations"]
            }
        
        # Ultimate fallback
        return self._create_fallback_analysis("No similar fields found", "")
    
    def _create_fallback_analysis(self, reason: str, raw_response: str = "") -> Dict[str, Any]:
        """Create a consistent fallback analysis structure"""
        return {
            "success": True,
            "ai_powered": False,
            "field_purpose": "Unknown field - requires manual review",
            "recommended_mapping": {
                "ghl_field_key": "special_requests__notes",
                "ghl_field_name": "Special Requests / Notes", 
                "confidence": "low"
            },
            "reasoning": reason,
            "raw_response": raw_response,
            "create_new_field": {
                "recommended": True,
                "reason": "Unknown field may need custom GHL field"
            }
        }
    
    async def analyze_form_fields_batch_v2(self, 
                                          form_data: Dict[str, Any], 
                                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        V2 batch field analysis with improved efficiency and caching
        
        Returns comprehensive mapping suggestions for the entire form
        """
        
        logger.info(f"🤖 V2 batch analyzing {len(form_data)} form fields")
        
        unknown_fields = {}
        known_mappings = {}
        cached_suggestions = 0
        
        # Separate known and unknown fields using existing field mapper
        for field_name, field_value in form_data.items():
            mapped_field = self.map_to_ghl_field(field_name)
            
            if mapped_field == field_name:  # No mapping found
                unknown_fields[field_name] = field_value
            else:
                known_mappings[field_name] = mapped_field
        
        # Analyze unknown fields with V2 AI/caching
        ai_analyses = {}
        if unknown_fields:
            logger.info(f"🤖 Found {len(unknown_fields)} unknown fields for V2 analysis")
            
            # Enhanced context for batch analysis
            batch_context = {
                **(context or {}),
                "form_data": form_data,
                "batch_analysis": True,
                "total_fields": len(form_data)
            }
            
            for field_name, field_value in unknown_fields.items():
                analysis = await self.analyze_unknown_field_with_ai(
                    field_name, field_value, batch_context
                )
                ai_analyses[field_name] = analysis
                
                if analysis.get("cache_hit"):
                    cached_suggestions += 1
        
        # Compile V2 results with enhanced metrics
        return {
            "total_fields": len(form_data),
            "known_mappings": known_mappings,
            "unknown_fields": list(unknown_fields.keys()),
            "ai_analyses": ai_analyses,
            "ai_enabled": self.ai_enabled,
            "mapping_recommendations": self._compile_mapping_recommendations_v2(ai_analyses),
            "suggested_new_mappings": self._extract_suggested_mappings_v2(ai_analyses),
            "analysis_timestamp": datetime.now().isoformat(),
            "v2_metrics": {
                "cached_suggestions": cached_suggestions,
                "ai_calls_made": len([a for a in ai_analyses.values() if a.get("ai_powered", False)]),
                "high_confidence_mappings": len([a for a in ai_analyses.values() 
                                               if a.get("recommended_mapping", {}).get("confidence") == "high"]),
                "cache_efficiency": (cached_suggestions / max(len(unknown_fields), 1) * 100) if unknown_fields else 0
            }
        }
    
    def _compile_mapping_recommendations_v2(self, ai_analyses: Dict[str, Any]) -> Dict[str, str]:
        """V2 mapping compilation with confidence thresholds"""
        
        recommendations = {}
        
        for field_name, analysis in ai_analyses.items():
            if analysis.get("success") and analysis.get("recommended_mapping"):
                mapping = analysis["recommended_mapping"]
                confidence = mapping.get("confidence", "low")
                
                # Only include medium+ confidence for automatic application
                if confidence in ["high", "medium"]:
                    recommendations[field_name] = mapping["ghl_field_key"]
        
        return recommendations
    
    def _extract_suggested_mappings_v2(self, ai_analyses: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """V2 mapping extraction with enhanced metadata"""
        
        suggested = {}
        
        for field_name, analysis in ai_analyses.items():
            if analysis.get("success") and analysis.get("recommended_mapping"):
                mapping = analysis["recommended_mapping"]
                confidence = mapping.get("confidence", "low")
                
                # Include all suggestions with metadata
                suggested[field_name] = {
                    "ghl_field": mapping["ghl_field_key"],
                    "confidence": confidence,
                    "reasoning": analysis.get("reasoning", ""),
                    "ai_powered": analysis.get("ai_powered", False),
                    "cache_hit": analysis.get("cache_hit", False),
                    "similarity_score": analysis.get("similarity_score"),
                    "suggested_at": datetime.now().isoformat()
                }
        
        return suggested
    
    async def auto_learn_from_form_submission_v2(self, 
                                                form_data: Dict[str, Any],
                                                context: Dict[str, Any] = None,
                                                auto_save: bool = False) -> Dict[str, Any]:
        """
        V2 auto-learning with improved accuracy and monitoring
        """
        
        logger.info(f"🧠 V2 auto-learning from form submission with {len(form_data)} fields")
        
        # Analyze all fields with V2 improvements
        analysis_result = await self.analyze_form_fields_batch_v2(form_data, context)
        
        auto_saved_mappings = {}
        
        # V2 auto-save with stricter confidence requirements
        if auto_save and analysis_result.get("suggested_new_mappings"):
            for field_name, mapping_info in analysis_result["suggested_new_mappings"].items():
                confidence = mapping_info.get("confidence", "low")
                ai_powered = mapping_info.get("ai_powered", False)
                
                # Only auto-save high-confidence AI-powered suggestions
                if confidence == "high" and ai_powered:
                    # Add to default mappings
                    self._mappings["default_mappings"][field_name] = mapping_info["ghl_field"]
                    auto_saved_mappings[field_name] = mapping_info["ghl_field"]
                    self.auto_saved_mappings += 1
                    logger.info(f"🔧 V2 auto-saved high-confidence mapping: {field_name} → {mapping_info['ghl_field']}")
            
            if auto_saved_mappings:
                self.save_mappings()
                logger.info(f"💾 V2 auto-saved {len(auto_saved_mappings)} new field mappings")
        
        return {
            **analysis_result,
            "auto_save_enabled": auto_save,
            "auto_saved_mappings": auto_saved_mappings,
            "learning_summary": {
                "total_analyzed": len(analysis_result.get("ai_analyses", {})),
                "high_confidence": len([a for a in analysis_result.get("ai_analyses", {}).values() 
                                      if a.get("recommended_mapping", {}).get("confidence") == "high"]),
                "auto_saved": len(auto_saved_mappings),
                "cache_efficiency": analysis_result["v2_metrics"]["cache_efficiency"]
            }
        }
    
    def get_v2_enhanced_stats(self) -> Dict[str, Any]:
        """V2 enhanced statistics with field reference service integration"""
        
        base_stats = self.get_mapping_stats()
        field_service_stats = self.field_reference_service.get_field_statistics()
        
        return {
            **base_stats,
            "ai_enhanced": True,
            "version": "v2",
            "ai_field_analysis_enabled": self.ai_enabled,
            "anthropic_configured": bool(self.anthropic_client),
            "field_reference_service": field_service_stats,
            "v2_metrics": {
                "total_analyses": self.analysis_count,
                "auto_saved_mappings": self.auto_saved_mappings,
                "cache_hits": self.cache_hits,
                "cache_hit_rate": (self.cache_hits / max(self.analysis_count, 1) * 100) if self.analysis_count > 0 else 0
            },
            "features": {
                "unknown_field_analysis": self.ai_enabled,
                "batch_field_analysis": self.ai_enabled,
                "auto_learning": self.ai_enabled,
                "intelligent_suggestions": True,
                "field_similarity_matching": True,
                "marine_industry_context": True,
                "caching_optimization": True
            }
        }


# Global V2 enhanced instance
ai_enhanced_field_mapper_v2 = AIEnhancedFieldMapperV2()