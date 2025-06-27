"""
Data validation utilities for AI-Based Data Cleaner
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DataValidator:
    """Comprehensive data validation class"""
    
    def __init__(self):
        self.validation_rules = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\+]?[1-9][\d]{0,15}$',
            'url': r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$',
            'date': r'^\d{4}-\d{2}-\d{2}$|^\d{2}\/\d{2}\/\d{4}$|^\d{2}-\d{2}-\d{4}$'
        }
    
    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive validation of a DataFrame
        
        Args:
            df: pandas DataFrame to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_report = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'column_validations': {},
            'data_quality_score': 0.0
        }
        
        try:
            # Basic structure validation
            self._validate_structure(df, validation_report)
            
            # Column-wise validation
            for column in df.columns:
                column_validation = self._validate_column(df[column], column)
                validation_report['column_validations'][column] = column_validation
                
                # Aggregate issues
                if column_validation['issues']:
                    validation_report['issues'].extend(column_validation['issues'])
                if column_validation['warnings']:
                    validation_report['warnings'].extend(column_validation['warnings'])
            
            # Calculate overall data quality score
            validation_report['data_quality_score'] = self._calculate_quality_score(df, validation_report)
            
            # Determine if data is valid
            validation_report['is_valid'] = len(validation_report['issues']) == 0
            
            logger.info(f"Data validation completed. Quality score: {validation_report['data_quality_score']:.2f}")
            
        except Exception as e:
            logger.error(f"Error during data validation: {str(e)}")
            validation_report['issues'].append(f"Validation error: {str(e)}")
            validation_report['is_valid'] = False
        
        return validation_report
    
    def _validate_structure(self, df: pd.DataFrame, report: Dict):
        """Validate basic DataFrame structure"""
        
        # Check if DataFrame is empty
        if df.empty:
            report['issues'].append("DataFrame is empty")
            return
        
        # Check for unnamed columns
        unnamed_cols = [col for col in df.columns if str(col).startswith('Unnamed:')]
        if unnamed_cols:
            report['warnings'].append(f"Found {len(unnamed_cols)} unnamed columns: {unnamed_cols}")
        
        # Check for duplicate column names
        duplicate_cols = df.columns[df.columns.duplicated()].tolist()
        if duplicate_cols:
            report['issues'].append(f"Duplicate column names found: {duplicate_cols}")
        
        # Check for extremely wide datasets
        if df.shape[1] > 1000:
            report['warnings'].append(f"Dataset has {df.shape[1]} columns, which may impact performance")
        
        # Check for extremely long datasets
        if df.shape[0] > 1000000:
            report['warnings'].append(f"Dataset has {df.shape[0]} rows, which may impact performance")
    
    def _validate_column(self, series: pd.Series, column_name: str) -> Dict[str, Any]:
        """Validate individual column"""
        
        validation = {
            'column_name': column_name,
            'data_type': str(series.dtype),
            'issues': [],
            'warnings': [],
            'quality_metrics': {}
        }
        
        # Basic metrics
        total_count = len(series)
        null_count = series.isnull().sum()
        null_percentage = (null_count / total_count) * 100 if total_count > 0 else 0
        unique_count = series.nunique()
        
        validation['quality_metrics'] = {
            'total_count': total_count,
            'null_count': null_count,
            'null_percentage': null_percentage,
            'unique_count': unique_count,
            'completeness_score': 100 - null_percentage
        }
        
        # Check for high missing data
        if null_percentage > 50:
            validation['issues'].append(f"Column '{column_name}' has {null_percentage:.1f}% missing values")
        elif null_percentage > 20:
            validation['warnings'].append(f"Column '{column_name}' has {null_percentage:.1f}% missing values")
        
        # Check for single value columns
        if unique_count == 1 and null_count == 0:
            validation['warnings'].append(f"Column '{column_name}' contains only one unique value")
        
        # Type-specific validations
        if series.dtype == 'object':
            self._validate_text_column(series, column_name, validation)
        elif series.dtype in ['int64', 'float64']:
            self._validate_numeric_column(series, column_name, validation)
        
        return validation
    
    def _validate_text_column(self, series: pd.Series, column_name: str, validation: Dict):
        """Validate text/object columns"""
        
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return
        
        # Check for mixed data types in object column
        type_counts = {}
        for value in non_null_series.head(100):  # Sample for performance
            value_type = type(value).__name__
            type_counts[value_type] = type_counts.get(value_type, 0) + 1
        
        if len(type_counts) > 1:
            validation['warnings'].append(f"Column '{column_name}' contains mixed data types: {type_counts}")
        
        # Check string lengths for consistency
        if all(isinstance(x, str) for x in non_null_series.head(100)):
            lengths = non_null_series.astype(str).str.len()
            avg_length = lengths.mean()
            std_length = lengths.std()
            
            validation['quality_metrics']['avg_string_length'] = avg_length
            validation['quality_metrics']['string_length_std'] = std_length
            
            # Check for extremely long strings
            max_length = lengths.max()
            if max_length > 1000:
                validation['warnings'].append(f"Column '{column_name}' contains very long strings (max: {max_length} chars)")
            
            # Check for potential data format patterns
            self._detect_data_patterns(non_null_series, column_name, validation)
    
    def _validate_numeric_column(self, series: pd.Series, column_name: str, validation: Dict):
        """Validate numeric columns"""
        
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return
        
        # Basic numeric statistics
        validation['quality_metrics'].update({
            'mean': non_null_series.mean(),
            'median': non_null_series.median(),
            'std': non_null_series.std(),
            'min': non_null_series.min(),
            'max': non_null_series.max()
        })
        
        # Check for outliers
        Q1 = non_null_series.quantile(0.25)
        Q3 = non_null_series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = ((non_null_series < lower_bound) | (non_null_series > upper_bound)).sum()
        outlier_percentage = (outliers / len(non_null_series)) * 100
        
        validation['quality_metrics']['outlier_count'] = outliers
        validation['quality_metrics']['outlier_percentage'] = outlier_percentage
        
        if outlier_percentage > 10:
            validation['warnings'].append(f"Column '{column_name}' has {outlier_percentage:.1f}% outliers")
        
        # Check for negative values where they might not make sense
        if (non_null_series < 0).any():
            negative_count = (non_null_series < 0).sum()
            validation['quality_metrics']['negative_count'] = negative_count
            
            # Common columns that shouldn't have negative values
            if any(keyword in column_name.lower() for keyword in ['age', 'price', 'cost', 'amount', 'quantity', 'count']):
                validation['warnings'].append(f"Column '{column_name}' contains {negative_count} negative values")
    
    def _detect_data_patterns(self, series: pd.Series, column_name: str, validation: Dict):
        """Detect common data patterns in text columns"""
        
        sample_values = series.head(50).astype(str)
        
        # Check for email pattern
        email_matches = sum(1 for val in sample_values if re.match(self.validation_rules['email'], val))
        if email_matches > len(sample_values) * 0.8:
            validation['quality_metrics']['detected_pattern'] = 'email'
            
            # Validate all emails
            invalid_emails = sum(1 for val in series.dropna().astype(str) 
                               if not re.match(self.validation_rules['email'], val))
            if invalid_emails > 0:
                validation['warnings'].append(f"Column '{column_name}' appears to be emails but has {invalid_emails} invalid entries")
        
        # Check for phone pattern
        phone_matches = sum(1 for val in sample_values if re.match(self.validation_rules['phone'], val.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')))
        if phone_matches > len(sample_values) * 0.8:
            validation['quality_metrics']['detected_pattern'] = 'phone'
        
        # Check for URL pattern
        url_matches = sum(1 for val in sample_values if re.match(self.validation_rules['url'], val))
        if url_matches > len(sample_values) * 0.8:
            validation['quality_metrics']['detected_pattern'] = 'url'
        
        # Check for date pattern
        date_matches = sum(1 for val in sample_values if re.match(self.validation_rules['date'], val))
        if date_matches > len(sample_values) * 0.8:
            validation['quality_metrics']['detected_pattern'] = 'date'
    
    def _calculate_quality_score(self, df: pd.DataFrame, validation_report: Dict) -> float:
        """Calculate overall data quality score (0-100)"""
        
        if df.empty:
            return 0.0
        
        total_score = 0.0
        weights = {
            'completeness': 0.4,  # 40% weight for data completeness
            'consistency': 0.3,   # 30% weight for data consistency
            'validity': 0.2,      # 20% weight for data validity
            'uniqueness': 0.1     # 10% weight for uniqueness
        }
        
        # Completeness score (based on missing values)
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        completeness_score = ((total_cells - missing_cells) / total_cells) * 100 if total_cells > 0 else 0
        
        # Consistency score (based on data type consistency and patterns)
        consistency_score = 100.0
        for col_validation in validation_report['column_validations'].values():
            if 'mixed data types' in str(col_validation.get('warnings', [])):
                consistency_score -= 10
        
        # Validity score (based on detected issues)
        validity_score = 100.0
        issue_count = len(validation_report['issues'])
        validity_score = max(0, validity_score - (issue_count * 10))
        
        # Uniqueness score (based on duplicate rows)
        duplicate_percentage = (df.duplicated().sum() / len(df)) * 100 if len(df) > 0 else 0
        uniqueness_score = max(0, 100 - duplicate_percentage)
        
        # Calculate weighted average
        total_score = (
            completeness_score * weights['completeness'] +
            consistency_score * weights['consistency'] +
            validity_score * weights['validity'] +
            uniqueness_score * weights['uniqueness']
        )
        
        return round(total_score, 2)
