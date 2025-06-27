import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from data_processor import DataProcessor
from ai_cleaner import AICleaner
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class CleaningEngine:
    """Main engine for orchestrating data cleaning operations"""
    
    def __init__(self):
        """Initialize cleaning engine with required components"""
        self.data_processor = DataProcessor()
        self.ai_cleaner = AICleaner()
        self.cleaning_report = {
            'changes': [],
            'statistics': {},
            'errors': []
        }
    
    def clean_dataset(self, df: pd.DataFrame, cleaning_options: Dict[str, bool]) -> Tuple[pd.DataFrame, Dict]:
        """
        Main method to clean the entire dataset
        
        Args:
            df: Original pandas DataFrame
            cleaning_options: Dictionary of cleaning options to apply
            
        Returns:
            Tuple of (cleaned_dataframe, cleaning_report)
        """
        logger.info(f"Starting data cleaning process for dataset with shape {df.shape}")
        
        # Initialize cleaned dataframe
        cleaned_df = df.copy()
        self.cleaning_report = {'changes': [], 'statistics': {}, 'errors': []}
        
        # Store original statistics
        original_analysis = self.data_processor.analyze_data_quality(df)
        self.cleaning_report['statistics']['original'] = original_analysis
        
        try:
            # 1. Remove duplicate rows
            if cleaning_options.get('remove_duplicates', True):
                cleaned_df, duplicate_changes = self._remove_duplicates(cleaned_df)
                self.cleaning_report['changes'].extend(duplicate_changes)
            
            # 2. Clean text columns with AI
            if cleaning_options.get('ai_text_cleaning', True):
                cleaned_df = self._clean_text_columns(cleaned_df)
            
            # 3. Handle missing values
            if cleaning_options.get('fill_missing_values', True):
                cleaned_df = self._handle_missing_values(cleaned_df, cleaning_options)
            
            # 4. Fix data types
            if cleaning_options.get('fix_data_types', True):
                cleaned_df = self._fix_data_types(cleaned_df)
            
            # 5. Handle outliers
            if cleaning_options.get('handle_outliers', False):
                cleaned_df = self._handle_outliers(cleaned_df)
            
            # Generate final statistics
            final_analysis = self.data_processor.analyze_data_quality(cleaned_df)
            self.cleaning_report['statistics']['cleaned'] = final_analysis
            self.cleaning_report['statistics']['summary'] = self._generate_summary_stats(
                original_analysis, final_analysis
            )
            
            logger.info(f"Data cleaning completed. Applied {len(self.cleaning_report['changes'])} changes")
            
        except Exception as e:
            error_msg = f"Error during data cleaning: {str(e)}"
            logger.error(error_msg)
            self.cleaning_report['errors'].append(error_msg)
        
        return cleaned_df, self.cleaning_report
    
    def _remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict]]:
        """Remove duplicate rows from dataframe"""
        changes = []
        original_count = len(df)
        
        # Identify duplicates
        duplicate_mask = df.duplicated()
        duplicate_count = duplicate_mask.sum()
        
        if duplicate_count > 0:
            # Remove duplicates
            cleaned_df = df.drop_duplicates()
            changes.append({
                'type': 'duplicate_removal',
                'original_rows': original_count,
                'removed_rows': duplicate_count,
                'final_rows': len(cleaned_df)
            })
            logger.info(f"Removed {duplicate_count} duplicate rows")
            return cleaned_df, changes
        
        return df, changes
    
    def _clean_text_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean text columns using AI"""
        cleaned_df = df.copy()
        
        # Identify text columns
        text_columns = [col for col in df.columns if df[col].dtype == 'object']
        
        for col in text_columns:
            # Skip if column has too many unique values (likely not categorical)
            if df[col].nunique() > Config.MAX_ROWS_FOR_AI_PROCESSING:
                logger.info(f"Skipping AI cleaning for column '{col}' - too many unique values")
                continue
            
            try:
                cleaned_series, changes = self.ai_cleaner.clean_text_column(df[col], col)
                cleaned_df[col] = cleaned_series
                self.cleaning_report['changes'].extend(changes)
                
            except Exception as e:
                error_msg = f"Error cleaning text column '{col}': {str(e)}"
                logger.error(error_msg)
                self.cleaning_report['errors'].append(error_msg)
        
        return cleaned_df
    
    def _handle_missing_values(self, df: pd.DataFrame, options: Dict[str, bool]) -> pd.DataFrame:
        """Handle missing values using various strategies"""
        cleaned_df = df.copy()
        
        for col in df.columns:
            if df[col].isnull().sum() == 0:
                continue
            
            try:
                if df[col].dtype in ['int64', 'float64']:
                    # Numeric columns
                    cleaned_df[col] = self._fill_numeric_missing(df[col], col, options)
                elif df[col].dtype == 'object':
                    # Text columns
                    cleaned_df[col] = self._fill_text_missing(df[col], col, options)
                else:
                    # Other types - forward fill
                    cleaned_df[col] = df[col].fillna(method='ffill')
                    
            except Exception as e:
                error_msg = f"Error handling missing values in column '{col}': {str(e)}"
                logger.error(error_msg)
                self.cleaning_report['errors'].append(error_msg)
        
        return cleaned_df
    
    def _fill_numeric_missing(self, series: pd.Series, col_name: str, options: Dict) -> pd.Series:
        """Fill missing values in numeric columns"""
        missing_count = series.isnull().sum()
        
        if options.get('use_ai_for_missing', False) and missing_count <= 10:
            # Use AI for small number of missing values
            try:
                filled_series, changes = self.ai_cleaner.suggest_missing_values(series, col_name)
                self.cleaning_report['changes'].extend(changes)
                return filled_series
            except Exception as e:
                logger.warning(f"AI filling failed for {col_name}, falling back to statistical method")
        
        # Use statistical methods
        if series.std() / series.mean() < 0.5:  # Low variance - use mean
            fill_value = series.mean()
            method = 'mean'
        else:  # High variance - use median
            fill_value = series.median()
            method = 'median'
        
        filled_series = series.fillna(fill_value)
        
        self.cleaning_report['changes'].append({
            'type': 'missing_value_fill',
            'column': col_name,
            'method': method,
            'fill_value': fill_value,
            'count': missing_count
        })
        
        return filled_series
    
    def _fill_text_missing(self, series: pd.Series, col_name: str, options: Dict) -> pd.Series:
        """Fill missing values in text columns"""
        missing_count = series.isnull().sum()
        
        if options.get('use_ai_for_missing', False) and missing_count <= 5:
            # Use AI for small number of missing values
            try:
                filled_series, changes = self.ai_cleaner.suggest_missing_values(series, col_name)
                self.cleaning_report['changes'].extend(changes)
                return filled_series
            except Exception as e:
                logger.warning(f"AI filling failed for {col_name}, falling back to mode")
        
        # Use mode (most frequent value)
        mode_value = series.mode()
        if len(mode_value) > 0:
            fill_value = mode_value.iloc[0]
        else:
            fill_value = "Unknown"
        
        filled_series = series.fillna(fill_value)
        
        self.cleaning_report['changes'].append({
            'type': 'missing_value_fill',
            'column': col_name,
            'method': 'mode',
            'fill_value': fill_value,
            'count': missing_count
        })
        
        return filled_series
    
    def _fix_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix and optimize data types"""
        cleaned_df = df.copy()
        type_suggestions = self.data_processor.detect_data_types(df)
        
        for col, suggested_type in type_suggestions.items():
            current_type = str(df[col].dtype)
            
            if current_type != suggested_type:
                try:
                    if suggested_type == 'int64':
                        cleaned_df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                    elif suggested_type == 'float64':
                        cleaned_df[col] = pd.to_numeric(df[col], errors='coerce')
                    elif suggested_type == 'datetime64[ns]':
                        cleaned_df[col] = pd.to_datetime(df[col], errors='coerce')
                    elif suggested_type == 'bool':
                        cleaned_df[col] = df[col].astype(str).str.lower().map({
                            'true': True, 'false': False, '1': True, '0': False,
                            'yes': True, 'no': False
                        })
                    
                    self.cleaning_report['changes'].append({
                        'type': 'data_type_conversion',
                        'column': col,
                        'from_type': current_type,
                        'to_type': suggested_type
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not convert column '{col}' to {suggested_type}: {str(e)}")
        
        return cleaned_df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle outliers in numeric columns"""
        cleaned_df = df.copy()
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_count = outlier_mask.sum()
            
            if outlier_count > 0:
                # Cap outliers at bounds
                cleaned_df.loc[df[col] < lower_bound, col] = lower_bound
                cleaned_df.loc[df[col] > upper_bound, col] = upper_bound
                
                self.cleaning_report['changes'].append({
                    'type': 'outlier_handling',
                    'column': col,
                    'outliers_capped': outlier_count,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                })
        
        return cleaned_df
    
    def _generate_summary_stats(self, original: Dict, cleaned: Dict) -> Dict:
        """Generate summary statistics comparing original and cleaned data"""
        summary = {
            'total_changes': len(self.cleaning_report['changes']),
            'rows_before': original['shape'][0],
            'rows_after': cleaned['shape'][0],
            'columns': original['shape'][1],
            'missing_values_before': sum(original['missing_values'].values()),
            'missing_values_after': sum(cleaned['missing_values'].values()),
            'duplicates_removed': original['duplicates']
        }
        
        summary['missing_reduction_percentage'] = (
            (summary['missing_values_before'] - summary['missing_values_after']) / 
            max(summary['missing_values_before'], 1) * 100
        )
        
        return summary
