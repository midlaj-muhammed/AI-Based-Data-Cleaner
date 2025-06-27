import pandas as pd
import numpy as np
import re
from datetime import datetime, date
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Any, Optional
import phonenumbers
from phonenumbers import NumberParseException
import logging
from dataclasses import dataclass
from utils.logger import setup_logger

logger = setup_logger(__name__)

@dataclass
class ValidationIssue:
    """Represents a data quality issue found during validation"""
    category: str
    severity: str  # 'HIGH', 'MEDIUM', 'LOW'
    description: str
    affected_records: List[int]
    examples: List[Dict[str, Any]]
    count: int
    recommendation: str

class AdvancedDataValidator:
    """
    Advanced data quality validator focusing on logical inconsistencies
    and business rule violations
    """
    
    def __init__(self, company_founding_year: int = 1990):
        """
        Initialize the advanced validator
        
        Args:
            company_founding_year: Year the company was founded (for join date validation)
        """
        self.company_founding_year = company_founding_year
        self.issues: List[ValidationIssue] = []
        self.current_year = datetime.now().year
        
    def validate_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform comprehensive advanced validation on the dataset
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dictionary containing validation results and detailed report
        """
        logger.info(f"Starting advanced validation on dataset with {len(df)} records")
        
        # Clear previous issues
        self.issues = []
        
        # Perform all validation checks
        self._detect_duplicate_identities(df)
        self._analyze_data_patterns(df)
        self._validate_business_logic(df)
        self._check_contextual_integrity(df)
        
        # Generate comprehensive report
        report = self._generate_validation_report(df)
        
        logger.info(f"Advanced validation completed. Found {len(self.issues)} issue categories")
        return report
    
    def _detect_duplicate_identities(self, df: pd.DataFrame):
        """Detect duplicate email addresses and phone numbers"""
        logger.info("Detecting duplicate identities...")
        
        # Email duplicate detection
        if 'email' in df.columns:
            self._check_duplicate_emails(df)
        
        # Phone number duplicate detection
        phone_columns = [col for col in df.columns if 'phone' in col.lower()]
        for col in phone_columns:
            self._check_duplicate_phones(df, col)
        
        # Contact information overlap
        self._check_contact_overlap(df)
    
    def _check_duplicate_emails(self, df: pd.DataFrame):
        """Check for duplicate email addresses"""
        if 'email' not in df.columns:
            return
            
        # Normalize emails (lowercase, strip whitespace)
        normalized_emails = df['email'].str.lower().str.strip()
        
        # Find duplicates
        email_counts = normalized_emails.value_counts()
        duplicates = email_counts[email_counts > 1]
        
        if len(duplicates) > 0:
            affected_records = []
            examples = []
            
            for email, count in duplicates.items():
                duplicate_indices = df[normalized_emails == email].index.tolist()
                affected_records.extend(duplicate_indices)
                
                # Add example
                example_records = df.loc[duplicate_indices].to_dict('records')
                examples.append({
                    'email': email,
                    'count': count,
                    'records': example_records[:3]  # Show first 3 examples
                })
            
            self.issues.append(ValidationIssue(
                category="Duplicate Email Addresses",
                severity="HIGH",
                description=f"Found {len(duplicates)} email addresses used by multiple records",
                affected_records=affected_records,
                examples=examples[:5],  # Show first 5 examples
                count=len(affected_records),
                recommendation="Review duplicate emails for data entry errors or legitimate shared accounts. Consider implementing unique email constraints."
            ))
    
    def _check_duplicate_phones(self, df: pd.DataFrame, phone_column: str):
        """Check for duplicate phone numbers with normalization"""
        if phone_column not in df.columns:
            return
            
        # Normalize phone numbers
        normalized_phones = []
        parse_errors = []
        
        for idx, phone in df[phone_column].items():
            if pd.isna(phone):
                normalized_phones.append(None)
                continue
                
            try:
                # Try to parse and format phone number
                parsed = phonenumbers.parse(str(phone), "US")  # Assume US if no country code
                if phonenumbers.is_valid_number(parsed):
                    normalized = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                    normalized_phones.append(normalized)
                else:
                    # Fallback: remove all non-digits
                    digits_only = re.sub(r'\D', '', str(phone))
                    normalized_phones.append(digits_only if digits_only else None)
            except NumberParseException:
                # Fallback: remove all non-digits
                digits_only = re.sub(r'\D', '', str(phone))
                normalized_phones.append(digits_only if digits_only else None)
                parse_errors.append(idx)
        
        # Create series with normalized phones
        normalized_series = pd.Series(normalized_phones, index=df.index)
        
        # Find duplicates (excluding None values)
        valid_phones = normalized_series.dropna()
        phone_counts = valid_phones.value_counts()
        duplicates = phone_counts[phone_counts > 1]
        
        if len(duplicates) > 0:
            affected_records = []
            examples = []
            
            for phone, count in duplicates.items():
                duplicate_indices = df[normalized_series == phone].index.tolist()
                affected_records.extend(duplicate_indices)
                
                # Add example
                example_records = df.loc[duplicate_indices].to_dict('records')
                examples.append({
                    'normalized_phone': phone,
                    'count': count,
                    'records': example_records[:3]
                })
            
            self.issues.append(ValidationIssue(
                category=f"Duplicate Phone Numbers ({phone_column})",
                severity="HIGH",
                description=f"Found {len(duplicates)} phone numbers used by multiple records",
                affected_records=affected_records,
                examples=examples[:5],
                count=len(affected_records),
                recommendation="Review duplicate phone numbers for data entry errors or shared contact information. Consider business rules for shared phones."
            ))
    
    def _check_contact_overlap(self, df: pd.DataFrame):
        """Check for records sharing multiple contact methods"""
        if 'email' not in df.columns:
            return
            
        phone_columns = [col for col in df.columns if 'phone' in col.lower()]
        if not phone_columns:
            return
            
        # Group by email and check for multiple records with same phone
        overlaps = []
        
        for email in df['email'].unique():
            if pd.isna(email):
                continue
                
            email_records = df[df['email'] == email]
            if len(email_records) > 1:
                # Check if they also share phone numbers
                for phone_col in phone_columns:
                    phones = email_records[phone_col].dropna().unique()
                    if len(phones) == 1 and len(email_records) > 1:
                        overlaps.append({
                            'email': email,
                            'phone': phones[0],
                            'phone_column': phone_col,
                            'record_count': len(email_records),
                            'indices': email_records.index.tolist()
                        })
        
        if overlaps:
            affected_records = []
            for overlap in overlaps:
                affected_records.extend(overlap['indices'])
            
            self.issues.append(ValidationIssue(
                category="Complete Contact Information Overlap",
                severity="MEDIUM",
                description=f"Found {len(overlaps)} cases where multiple records share both email and phone",
                affected_records=affected_records,
                examples=overlaps[:5],
                count=len(affected_records),
                recommendation="These may be legitimate duplicates or data entry errors. Review for consolidation opportunities."
            ))
    
    def _analyze_data_patterns(self, df: pd.DataFrame):
        """Analyze data patterns for anomalies"""
        logger.info("Analyzing data patterns for anomalies...")
        
        # Age distribution analysis
        if 'age' in df.columns:
            self._analyze_age_patterns(df)
        
        # Date clustering analysis
        date_columns = [col for col in df.columns if 'date' in col.lower() or col.lower() in ['dob', 'birth_date', 'birthdate']]
        for col in date_columns:
            self._analyze_date_clustering(df, col)
    
    def _analyze_age_patterns(self, df: pd.DataFrame):
        """Analyze age distribution for suspicious patterns"""
        if 'age' not in df.columns:
            return
            
        ages = df['age'].dropna()
        if len(ages) == 0:
            return
        
        # Check for excessive rounding (ages ending in 0 or 5)
        rounded_ages = ages[ages % 5 == 0]
        rounded_percentage = len(rounded_ages) / len(ages) * 100
        
        if rounded_percentage > 40:  # More than 40% rounded ages is suspicious
            examples = df[df['age'] % 5 == 0].head(10).to_dict('records')
            
            self.issues.append(ValidationIssue(
                category="Suspicious Age Rounding",
                severity="MEDIUM",
                description=f"{rounded_percentage:.1f}% of ages are rounded to multiples of 5, suggesting artificial data",
                affected_records=df[df['age'] % 5 == 0].index.tolist(),
                examples=examples,
                count=len(rounded_ages),
                recommendation="Review age data collection process. Consider if ages were estimated rather than calculated from birthdates."
            ))
        
        # Check for unrealistic age clustering
        age_counts = ages.value_counts()
        max_count = age_counts.max()
        total_unique_ages = len(age_counts)
        
        if max_count > len(ages) * 0.1 and total_unique_ages > 10:  # More than 10% have same age
            most_common_age = age_counts.index[0]
            examples = df[df['age'] == most_common_age].head(10).to_dict('records')
            
            self.issues.append(ValidationIssue(
                category="Excessive Age Clustering",
                severity="MEDIUM",
                description=f"Age {most_common_age} appears {max_count} times ({max_count/len(ages)*100:.1f}% of records)",
                affected_records=df[df['age'] == most_common_age].index.tolist(),
                examples=examples,
                count=max_count,
                recommendation="Investigate why this specific age is so common. May indicate default value usage or data entry errors."
            ))

    def _analyze_date_clustering(self, df: pd.DataFrame, date_column: str):
        """Analyze date fields for suspicious clustering patterns"""
        if date_column not in df.columns:
            return

        # Convert to datetime if not already
        try:
            dates = pd.to_datetime(df[date_column], errors='coerce').dropna()
        except:
            return

        if len(dates) == 0:
            return

        # Check for January 1st clustering (common default date)
        jan_1_dates = dates[dates.dt.strftime('%m-%d') == '01-01']
        jan_1_percentage = len(jan_1_dates) / len(dates) * 100

        if jan_1_percentage > 20:  # More than 20% on January 1st
            examples = df[pd.to_datetime(df[date_column], errors='coerce').dt.strftime('%m-%d') == '01-01'].head(10).to_dict('records')

            self.issues.append(ValidationIssue(
                category=f"Suspicious Date Clustering - January 1st ({date_column})",
                severity="MEDIUM",
                description=f"{jan_1_percentage:.1f}% of {date_column} values are January 1st, suggesting default values",
                affected_records=df[pd.to_datetime(df[date_column], errors='coerce').dt.strftime('%m-%d') == '01-01'].index.tolist(),
                examples=examples,
                count=len(jan_1_dates),
                recommendation="Review data collection process. January 1st clustering often indicates missing or unknown dates filled with defaults."
            ))

        # Check for excessive clustering on specific dates
        date_counts = dates.dt.date.value_counts()
        max_count = date_counts.max()

        if max_count > len(dates) * 0.05 and len(date_counts) > 20:  # More than 5% on same date
            most_common_date = date_counts.index[0]
            examples = df[pd.to_datetime(df[date_column], errors='coerce').dt.date == most_common_date].head(10).to_dict('records')

            self.issues.append(ValidationIssue(
                category=f"Excessive Date Clustering ({date_column})",
                severity="MEDIUM",
                description=f"Date {most_common_date} appears {max_count} times ({max_count/len(dates)*100:.1f}% of records)",
                affected_records=df[pd.to_datetime(df[date_column], errors='coerce').dt.date == most_common_date].index.tolist(),
                examples=examples,
                count=max_count,
                recommendation="Investigate clustering around this specific date. May indicate bulk data imports or system-generated dates."
            ))

    def _validate_business_logic(self, df: pd.DataFrame):
        """Validate business logic rules"""
        logger.info("Validating business logic rules...")

        # Join date validation
        join_date_columns = [col for col in df.columns if 'join' in col.lower() or 'hire' in col.lower() or 'start' in col.lower()]
        for col in join_date_columns:
            self._validate_join_dates(df, col)

        # Age vs birthdate consistency
        if 'age' in df.columns and any('birth' in col.lower() or 'dob' in col.lower() for col in df.columns):
            self._validate_age_birthdate_consistency(df)

        # Temporal relationship validation
        self._validate_temporal_relationships(df)

    def _validate_join_dates(self, df: pd.DataFrame, join_column: str):
        """Validate join dates for business logic"""
        if join_column not in df.columns:
            return

        try:
            join_dates = pd.to_datetime(df[join_column], errors='coerce')
        except:
            return

        current_date = datetime.now()
        company_founding = datetime(self.company_founding_year, 1, 1)

        # Future join dates
        future_joins = df[join_dates > current_date]
        if len(future_joins) > 0:
            examples = future_joins.head(10).to_dict('records')

            self.issues.append(ValidationIssue(
                category=f"Future Join Dates ({join_column})",
                severity="HIGH",
                description=f"Found {len(future_joins)} records with join dates in the future",
                affected_records=future_joins.index.tolist(),
                examples=examples,
                count=len(future_joins),
                recommendation="Review and correct future join dates. These are likely data entry errors."
            ))

        # Join dates before company founding
        early_joins = df[join_dates < company_founding]
        if len(early_joins) > 0:
            examples = early_joins.head(10).to_dict('records')

            self.issues.append(ValidationIssue(
                category=f"Join Dates Before Company Founding ({join_column})",
                severity="HIGH",
                description=f"Found {len(early_joins)} records with join dates before company founding ({self.company_founding_year})",
                affected_records=early_joins.index.tolist(),
                examples=examples,
                count=len(early_joins),
                recommendation="Verify company founding year or correct impossible join dates."
            ))

    def _validate_age_birthdate_consistency(self, df: pd.DataFrame):
        """Validate consistency between age and birthdate"""
        age_col = 'age'
        birth_cols = [col for col in df.columns if 'birth' in col.lower() or 'dob' in col.lower()]

        if not birth_cols or age_col not in df.columns:
            return

        birth_col = birth_cols[0]  # Use first birthdate column found

        try:
            birth_dates = pd.to_datetime(df[birth_col], errors='coerce')
            ages = df[age_col]
        except:
            return

        # Calculate age from birthdate
        current_date = datetime.now()
        calculated_ages = ((current_date - birth_dates).dt.days / 365.25).round().astype('Int64')

        # Find inconsistencies (allow 1 year tolerance for birthday timing)
        inconsistent = df[abs(ages - calculated_ages) > 1]

        if len(inconsistent) > 0:
            examples = []
            for idx, row in inconsistent.head(10).iterrows():
                examples.append({
                    'record_index': idx,
                    'stated_age': row[age_col],
                    'calculated_age': calculated_ages.loc[idx],
                    'birthdate': row[birth_col],
                    'difference': abs(row[age_col] - calculated_ages.loc[idx])
                })

            self.issues.append(ValidationIssue(
                category="Age-Birthdate Inconsistency",
                severity="MEDIUM",
                description=f"Found {len(inconsistent)} records where stated age doesn't match calculated age from birthdate",
                affected_records=inconsistent.index.tolist(),
                examples=examples,
                count=len(inconsistent),
                recommendation="Review age calculation logic or data entry processes. Consider using birthdate as single source of truth for age."
            ))

    def _validate_temporal_relationships(self, df: pd.DataFrame):
        """Validate temporal relationships between date fields"""
        # Find birth and join date columns
        birth_cols = [col for col in df.columns if 'birth' in col.lower() or 'dob' in col.lower()]
        join_cols = [col for col in df.columns if 'join' in col.lower() or 'hire' in col.lower() or 'start' in col.lower()]

        if not birth_cols or not join_cols:
            return

        birth_col = birth_cols[0]
        join_col = join_cols[0]

        try:
            birth_dates = pd.to_datetime(df[birth_col], errors='coerce')
            join_dates = pd.to_datetime(df[join_col], errors='coerce')
        except:
            return

        # Check for join dates before birth dates (impossible)
        impossible = df[(join_dates < birth_dates) & birth_dates.notna() & join_dates.notna()]

        if len(impossible) > 0:
            examples = impossible.head(10).to_dict('records')

            self.issues.append(ValidationIssue(
                category="Impossible Date Relationships",
                severity="HIGH",
                description=f"Found {len(impossible)} records where join date is before birth date",
                affected_records=impossible.index.tolist(),
                examples=examples,
                count=len(impossible),
                recommendation="Critical data error: Join dates cannot be before birth dates. Review and correct these records immediately."
            ))

        # Check for unreasonably young employees (joined before age 16)
        young_joins = df[((join_dates - birth_dates).dt.days / 365.25 < 16) & birth_dates.notna() & join_dates.notna()]

        if len(young_joins) > 0:
            examples = []
            for idx, row in young_joins.head(10).iterrows():
                age_at_join = (join_dates.loc[idx] - birth_dates.loc[idx]).days / 365.25
                examples.append({
                    'record_index': idx,
                    'birth_date': birth_dates.loc[idx],
                    'join_date': join_dates.loc[idx],
                    'age_at_join': round(age_at_join, 1)
                })

            self.issues.append(ValidationIssue(
                category="Unreasonably Young Employees",
                severity="MEDIUM",
                description=f"Found {len(young_joins)} records where employees joined before age 16",
                affected_records=young_joins.index.tolist(),
                examples=examples,
                count=len(young_joins),
                recommendation="Review hiring policies and data accuracy. Consider if these are data entry errors or special cases (internships, etc.)."
            ))

    def _check_contextual_integrity(self, df: pd.DataFrame):
        """Check contextual data integrity"""
        logger.info("Checking contextual data integrity...")

        # Bulk import pattern detection
        join_cols = [col for col in df.columns if 'join' in col.lower() or 'hire' in col.lower() or 'start' in col.lower()]
        for col in join_cols:
            self._detect_bulk_import_patterns(df, col)

        # Age range validation
        if 'age' in df.columns:
            self._validate_age_ranges(df)

        # Employment duration analysis
        self._analyze_employment_duration(df)

    def _detect_bulk_import_patterns(self, df: pd.DataFrame, date_column: str):
        """Detect patterns suggesting bulk data imports"""
        if date_column not in df.columns:
            return

        try:
            dates = pd.to_datetime(df[date_column], errors='coerce').dropna()
        except:
            return

        if len(dates) == 0:
            return

        # Group by month-year and look for unusual spikes
        monthly_counts = dates.dt.to_period('M').value_counts().sort_index()

        if len(monthly_counts) > 1:
            mean_monthly = monthly_counts.mean()
            std_monthly = monthly_counts.std()

            # Find months with unusually high activity (more than 2 standard deviations above mean)
            threshold = mean_monthly + (2 * std_monthly)
            spike_months = monthly_counts[monthly_counts > threshold]

            if len(spike_months) > 0:
                examples = []
                for period, count in spike_months.head(5).items():
                    month_data = df[pd.to_datetime(df[date_column], errors='coerce').dt.to_period('M') == period]
                    examples.append({
                        'period': str(period),
                        'count': count,
                        'percentage_of_total': round(count / len(dates) * 100, 1),
                        'sample_records': month_data.head(3).to_dict('records')
                    })

                affected_records = []
                for period in spike_months.index:
                    period_records = df[pd.to_datetime(df[date_column], errors='coerce').dt.to_period('M') == period]
                    affected_records.extend(period_records.index.tolist())

                self.issues.append(ValidationIssue(
                    category=f"Bulk Import Pattern Detection ({date_column})",
                    severity="LOW",
                    description=f"Detected {len(spike_months)} months with unusually high {date_column} activity, suggesting bulk imports",
                    affected_records=affected_records,
                    examples=examples,
                    count=sum(spike_months),
                    recommendation="Review data import processes. Bulk imports may indicate data migration or system changes that should be documented."
                ))

    def _validate_age_ranges(self, df: pd.DataFrame):
        """Validate that ages fall within reasonable working ranges"""
        if 'age' not in df.columns:
            return

        ages = df['age'].dropna()

        # Check for unreasonably young employees (under 16)
        too_young = df[df['age'] < 16]
        if len(too_young) > 0:
            examples = too_young.head(10).to_dict('records')

            self.issues.append(ValidationIssue(
                category="Unreasonably Young Ages",
                severity="HIGH",
                description=f"Found {len(too_young)} records with ages under 16",
                affected_records=too_young.index.tolist(),
                examples=examples,
                count=len(too_young),
                recommendation="Review minimum age policies and data accuracy. Ages under 16 are unusual for employment records."
            ))

        # Check for unreasonably old employees (over 80)
        too_old = df[df['age'] > 80]
        if len(too_old) > 0:
            examples = too_old.head(10).to_dict('records')

            self.issues.append(ValidationIssue(
                category="Unreasonably Old Ages",
                severity="MEDIUM",
                description=f"Found {len(too_old)} records with ages over 80",
                affected_records=too_old.index.tolist(),
                examples=examples,
                count=len(too_old),
                recommendation="Review retirement policies and data accuracy. Ages over 80 may indicate data entry errors or special employment arrangements."
            ))

    def _analyze_employment_duration(self, df: pd.DataFrame):
        """Analyze employment duration patterns"""
        join_cols = [col for col in df.columns if 'join' in col.lower() or 'hire' in col.lower() or 'start' in col.lower()]

        if not join_cols:
            return

        join_col = join_cols[0]

        try:
            join_dates = pd.to_datetime(df[join_col], errors='coerce')
            current_date = datetime.now()

            # Calculate employment duration in years
            employment_duration = ((current_date - join_dates).dt.days / 365.25)

            # Check for unusually long employment (over 50 years)
            very_long = df[employment_duration > 50]
            if len(very_long) > 0:
                examples = []
                for idx, row in very_long.head(10).iterrows():
                    duration = employment_duration.loc[idx]
                    examples.append({
                        'record_index': idx,
                        'join_date': join_dates.loc[idx],
                        'duration_years': round(duration, 1)
                    })

                self.issues.append(ValidationIssue(
                    category="Unusually Long Employment Duration",
                    severity="MEDIUM",
                    description=f"Found {len(very_long)} records with employment duration over 50 years",
                    affected_records=very_long.index.tolist(),
                    examples=examples,
                    count=len(very_long),
                    recommendation="Review join dates for accuracy. Employment over 50 years may indicate data entry errors or legacy system issues."
                ))

        except Exception as e:
            logger.warning(f"Could not analyze employment duration: {e}")

    def _generate_validation_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info("Generating validation report...")

        # Categorize issues by severity
        high_severity = [issue for issue in self.issues if issue.severity == "HIGH"]
        medium_severity = [issue for issue in self.issues if issue.severity == "MEDIUM"]
        low_severity = [issue for issue in self.issues if issue.severity == "LOW"]

        # Calculate overall data quality score
        total_records = len(df)
        total_affected = len(set().union(*[issue.affected_records for issue in self.issues]))

        quality_score = max(0, 100 - (total_affected / total_records * 100)) if total_records > 0 else 100

        # Generate summary statistics
        summary = {
            'total_records': total_records,
            'total_issues_found': len(self.issues),
            'high_severity_issues': len(high_severity),
            'medium_severity_issues': len(medium_severity),
            'low_severity_issues': len(low_severity),
            'total_affected_records': total_affected,
            'data_quality_score': round(quality_score, 1),
            'validation_timestamp': datetime.now().isoformat()
        }

        # Prepare detailed issues
        detailed_issues = []
        for issue in self.issues:
            detailed_issues.append({
                'category': issue.category,
                'severity': issue.severity,
                'description': issue.description,
                'count': issue.count,
                'affected_percentage': round(issue.count / total_records * 100, 2),
                'examples': issue.examples,
                'recommendation': issue.recommendation
            })

        # Generate recommendations by priority
        recommendations = []

        # High priority recommendations
        if high_severity:
            recommendations.append({
                'priority': 'HIGH',
                'title': 'Critical Data Issues Requiring Immediate Attention',
                'items': [issue.recommendation for issue in high_severity]
            })

        # Medium priority recommendations
        if medium_severity:
            recommendations.append({
                'priority': 'MEDIUM',
                'title': 'Data Quality Improvements',
                'items': [issue.recommendation for issue in medium_severity]
            })

        # Low priority recommendations
        if low_severity:
            recommendations.append({
                'priority': 'LOW',
                'title': 'Process Improvements and Monitoring',
                'items': [issue.recommendation for issue in low_severity]
            })

        return {
            'summary': summary,
            'detailed_issues': detailed_issues,
            'recommendations': recommendations,
            'validation_passed': len(high_severity) == 0,
            'issues_by_severity': {
                'high': [issue.__dict__ for issue in high_severity],
                'medium': [issue.__dict__ for issue in medium_severity],
                'low': [issue.__dict__ for issue in low_severity]
            }
        }
