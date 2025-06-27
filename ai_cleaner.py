import openai
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json
import time
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class AICleaner:
    """AI-powered data cleaning using OpenAI GPT API"""
    
    def __init__(self):
        """Initialize AI cleaner with OpenAI configuration"""
        try:
            Config.validate_config()
            openai.api_key = Config.OPENAI_API_KEY
            self.model = Config.OPENAI_MODEL
            self.max_tokens = Config.MAX_TOKENS
            self.temperature = Config.TEMPERATURE
            logger.info("AI Cleaner initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI Cleaner: {str(e)}")
            raise
    
    def clean_text_column(self, series: pd.Series, column_name: str) -> Tuple[pd.Series, List[Dict]]:
        """
        Clean text data in a column using AI
        
        Args:
            series: pandas Series containing text data
            column_name: Name of the column being cleaned
            
        Returns:
            Tuple of (cleaned_series, list_of_changes)
        """
        changes = []
        cleaned_series = series.copy()
        
        # Get sample of non-null values for analysis
        non_null_values = series.dropna().unique()
        if len(non_null_values) == 0:
            return cleaned_series, changes
        
        # Limit sample size for API efficiency
        sample_size = min(20, len(non_null_values))
        sample_values = non_null_values[:sample_size].tolist()
        
        try:
            # Create prompt for text cleaning
            prompt = self._create_text_cleaning_prompt(sample_values, column_name)
            
            # Get AI suggestions
            response = self._call_openai_api(prompt)
            suggestions = self._parse_cleaning_response(response)
            
            # Apply suggestions
            for original, cleaned in suggestions.items():
                if original != cleaned and original in series.values:
                    mask = series == original
                    cleaned_series.loc[mask] = cleaned
                    changes.append({
                        'type': 'text_cleaning',
                        'column': column_name,
                        'original': original,
                        'cleaned': cleaned,
                        'count': mask.sum()
                    })
            
            logger.info(f"Applied {len(changes)} text cleaning changes to column '{column_name}'")
            
        except Exception as e:
            logger.error(f"Error in AI text cleaning for column '{column_name}': {str(e)}")
        
        return cleaned_series, changes
    
    def suggest_missing_values(self, series: pd.Series, column_name: str, 
                             context_columns: Optional[List[str]] = None) -> Tuple[pd.Series, List[Dict]]:
        """
        Suggest values for missing data using AI
        
        Args:
            series: pandas Series with missing values
            column_name: Name of the column
            context_columns: List of related column names for context
            
        Returns:
            Tuple of (series_with_suggestions, list_of_changes)
        """
        changes = []
        filled_series = series.copy()
        
        missing_mask = series.isnull()
        if not missing_mask.any():
            return filled_series, changes
        
        # Get context for AI suggestions
        non_null_sample = series.dropna().head(10).tolist()
        if len(non_null_sample) < 3:
            logger.warning(f"Insufficient data for AI suggestions in column '{column_name}'")
            return filled_series, changes
        
        try:
            # Create prompt for missing value suggestions
            prompt = self._create_missing_value_prompt(non_null_sample, column_name, context_columns)
            
            # Get AI suggestions
            response = self._call_openai_api(prompt)
            suggestions = self._parse_missing_value_response(response, series.dtype)
            
            # Apply suggestions to missing values
            missing_indices = series[missing_mask].index
            suggestion_count = min(len(suggestions), len(missing_indices))
            
            for i in range(suggestion_count):
                idx = missing_indices[i]
                suggested_value = suggestions[i]
                filled_series.loc[idx] = suggested_value
                changes.append({
                    'type': 'missing_value_fill',
                    'column': column_name,
                    'index': idx,
                    'suggested_value': suggested_value
                })
            
            logger.info(f"Applied {len(changes)} AI suggestions for missing values in column '{column_name}'")
            
        except Exception as e:
            logger.error(f"Error in AI missing value suggestion for column '{column_name}': {str(e)}")
        
        return filled_series, changes
    
    def _create_text_cleaning_prompt(self, sample_values: List[str], column_name: str) -> str:
        """Create prompt for text cleaning"""
        prompt = f"""
You are a data cleaning expert. I have a column named '{column_name}' with the following sample values:

{json.dumps(sample_values, indent=2)}

Please clean these text values by:
1. Fixing spelling errors
2. Standardizing capitalization
3. Removing extra whitespace
4. Fixing common typos

Return a JSON object where keys are original values and values are cleaned versions.
Only include entries that need changes. If a value is already clean, don't include it.

Example format:
{{"original_value": "cleaned_value", "another_original": "another_cleaned"}}
"""
        return prompt
    
    def _create_missing_value_prompt(self, sample_values: List[Any], column_name: str, 
                                   context_columns: Optional[List[str]]) -> str:
        """Create prompt for missing value suggestions"""
        context_info = f" (related to columns: {', '.join(context_columns)})" if context_columns else ""
        
        prompt = f"""
You are a data analyst. I have a column named '{column_name}'{context_info} with these sample values:

{json.dumps(sample_values, indent=2)}

Based on the pattern and context, suggest 5 realistic values that could fill missing entries in this column.
The suggestions should be consistent with the existing data pattern and type.

Return a JSON array of suggested values:
["suggestion1", "suggestion2", "suggestion3", "suggestion4", "suggestion5"]
"""
        return prompt
    
    def _call_openai_api(self, prompt: str) -> str:
        """Make API call to OpenAI with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful data cleaning assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    raise
    
    def _parse_cleaning_response(self, response: str) -> Dict[str, str]:
        """Parse AI response for text cleaning suggestions"""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning("No valid JSON found in cleaning response")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cleaning response: {str(e)}")
            return {}
    
    def _parse_missing_value_response(self, response: str, dtype) -> List[Any]:
        """Parse AI response for missing value suggestions"""
        try:
            # Try to extract JSON array from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                suggestions = json.loads(json_str)
                
                # Convert suggestions to appropriate data type
                if dtype in ['int64', 'float64']:
                    suggestions = [pd.to_numeric(s, errors='coerce') for s in suggestions]
                    suggestions = [s for s in suggestions if not pd.isna(s)]
                
                return suggestions[:5]  # Limit to 5 suggestions
            else:
                logger.warning("No valid JSON array found in missing value response")
                return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse missing value response: {str(e)}")
            return []
