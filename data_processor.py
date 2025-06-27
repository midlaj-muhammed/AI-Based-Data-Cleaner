import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from utils.logger import setup_logger
import io

logger = setup_logger(__name__)

class DataProcessor:
    """Core data processing class for handling file operations and data analysis"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'xlsx', 'xls']
        
    def read_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """
        Read uploaded file and return pandas DataFrame
        
        Args:
            file_content: File content as bytes
            filename: Name of the uploaded file
            
        Returns:
            pandas DataFrame
            
        Raises:
            ValueError: If file format is not supported
            Exception: If file cannot be read
        """
        try:
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            if file_extension == 'csv':
                # Try different encodings for CSV files
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                        logger.info(f"Successfully read CSV file with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Could not decode CSV file with any supported encoding")
                    
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(file_content))
                logger.info(f"Successfully read Excel file: {filename}")
            
            logger.info(f"Loaded dataset with shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error reading file {filename}: {str(e)}")
            raise
    
    def analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze data quality and return comprehensive statistics
        
        Args:
            df: pandas DataFrame to analyze
            
        Returns:
            Dictionary containing data quality metrics
        """
        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': {},
            'duplicates': df.duplicated().sum(),
            'column_stats': {}
        }
        
        # Analyze each column
        for col in df.columns:
            col_analysis = {
                'dtype': str(df[col].dtype),
                'missing_count': df[col].isnull().sum(),
                'missing_percentage': (df[col].isnull().sum() / len(df)) * 100,
                'unique_values': df[col].nunique(),
                'sample_values': df[col].dropna().head(5).tolist()
            }
            
            # Add specific stats based on data type
            if df[col].dtype in ['int64', 'float64']:
                col_analysis.update({
                    'mean': df[col].mean(),
                    'median': df[col].median(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'outliers': self._detect_outliers(df[col])
                })
            elif df[col].dtype == 'object':
                col_analysis.update({
                    'most_common': df[col].value_counts().head(3).to_dict(),
                    'avg_length': df[col].astype(str).str.len().mean()
                })
            
            analysis['column_stats'][col] = col_analysis
            analysis['missing_values'][col] = col_analysis['missing_count']
        
        logger.info(f"Data quality analysis completed for {df.shape[0]} rows, {df.shape[1]} columns")
        return analysis
    
    def _detect_outliers(self, series: pd.Series) -> int:
        """
        Detect outliers using IQR method
        
        Args:
            series: pandas Series with numeric data
            
        Returns:
            Number of outliers detected
        """
        if series.dtype not in ['int64', 'float64']:
            return 0
            
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = ((series < lower_bound) | (series > upper_bound)).sum()
        return outliers
    
    def detect_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect and suggest optimal data types for each column
        
        Args:
            df: pandas DataFrame
            
        Returns:
            Dictionary mapping column names to suggested data types
        """
        suggestions = {}
        
        for col in df.columns:
            current_type = str(df[col].dtype)
            
            # Skip if already optimal
            if current_type in ['int64', 'float64', 'bool', 'datetime64[ns]']:
                suggestions[col] = current_type
                continue
            
            # Try to infer better type
            non_null_series = df[col].dropna()
            
            if len(non_null_series) == 0:
                suggestions[col] = 'object'
                continue
            
            # Check for numeric
            try:
                pd.to_numeric(non_null_series)
                if non_null_series.astype(str).str.contains(r'\.').any():
                    suggestions[col] = 'float64'
                else:
                    suggestions[col] = 'int64'
                continue
            except (ValueError, TypeError):
                pass
            
            # Check for datetime
            try:
                pd.to_datetime(non_null_series)
                suggestions[col] = 'datetime64[ns]'
                continue
            except (ValueError, TypeError):
                pass
            
            # Check for boolean
            unique_vals = set(non_null_series.astype(str).str.lower())
            if unique_vals.issubset({'true', 'false', '1', '0', 'yes', 'no'}):
                suggestions[col] = 'bool'
                continue
            
            suggestions[col] = 'object'
        
        return suggestions
