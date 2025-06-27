import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from advanced_validator import AdvancedDataValidator
from typing import Dict, Any
import json

def render_advanced_validation_tab(df: pd.DataFrame):
    """
    Render the advanced validation tab in Streamlit
    
    Args:
        df: DataFrame to validate
    """
    st.header("🔍 Advanced Data Quality Validation")
    st.markdown("""
    This advanced validation focuses on **logical inconsistencies** and **business rule violations** 
    rather than basic technical data issues. It performs deep analysis to detect:
    
    - **Duplicate Identity Detection**: Email and phone number duplicates with normalization
    - **Data Pattern Anomalies**: Suspicious clustering and artificial standardization
    - **Business Logic Violations**: Chronological inconsistencies and employment logic errors
    - **Contextual Integrity Issues**: Bulk import patterns and unrealistic data ranges
    """)
    
    # Configuration section
    with st.expander("⚙️ Validation Configuration", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            company_founding_year = st.number_input(
                "Company Founding Year",
                min_value=1800,
                max_value=2024,
                value=1990,
                help="Used to validate join dates aren't before company founding"
            )
        
        with col2:
            validation_scope = st.multiselect(
                "Validation Scope",
                ["Duplicate Detection", "Pattern Analysis", "Business Logic", "Contextual Integrity"],
                default=["Duplicate Detection", "Pattern Analysis", "Business Logic", "Contextual Integrity"],
                help="Select which validation categories to run"
            )
    
    # Run validation button
    if st.button("🚀 Run Advanced Validation", type="primary"):
        with st.spinner("Performing advanced data quality validation..."):
            # Initialize validator
            validator = AdvancedDataValidator(company_founding_year=company_founding_year)
            
            # Run validation
            validation_results = validator.validate_dataset(df)
            
            # Store results in session state
            st.session_state['validation_results'] = validation_results
            st.session_state['validator'] = validator
    
    # Display results if available
    if 'validation_results' in st.session_state:
        display_validation_results(st.session_state['validation_results'], df)

def display_validation_results(results: Dict[str, Any], df: pd.DataFrame):
    """Display comprehensive validation results"""
    
    # Summary metrics
    st.subheader("📊 Validation Summary")
    
    summary = results['summary']
    
    # Create metrics columns
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Data Quality Score", f"{summary['data_quality_score']}%")
    
    with col2:
        st.metric("Total Issues", summary['total_issues_found'])
    
    with col3:
        st.metric("High Severity", summary['high_severity_issues'], 
                 delta=f"-{summary['high_severity_issues']}" if summary['high_severity_issues'] > 0 else None)
    
    with col4:
        st.metric("Medium Severity", summary['medium_severity_issues'])
    
    with col5:
        st.metric("Affected Records", f"{summary['total_affected_records']} ({summary['total_affected_records']/summary['total_records']*100:.1f}%)")
    
    # Overall status
    if results['validation_passed']:
        st.success("✅ **Validation Passed**: No critical issues found!")
    else:
        st.error("❌ **Validation Failed**: Critical issues require immediate attention!")
    
    # Severity distribution chart
    if summary['total_issues_found'] > 0:
        st.subheader("📈 Issues by Severity")
        
        severity_data = {
            'Severity': ['High', 'Medium', 'Low'],
            'Count': [summary['high_severity_issues'], summary['medium_severity_issues'], summary['low_severity_issues']],
            'Color': ['#FF4B4B', '#FFA500', '#32CD32']
        }
        
        fig = px.bar(
            severity_data, 
            x='Severity', 
            y='Count',
            color='Color',
            color_discrete_map={color: color for color in severity_data['Color']},
            title="Distribution of Issues by Severity Level"
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed issues
    st.subheader("🔍 Detailed Issue Analysis")
    
    if results['detailed_issues']:
        # Create tabs for each severity level
        severity_tabs = []
        if summary['high_severity_issues'] > 0:
            severity_tabs.append("🔴 High Severity")
        if summary['medium_severity_issues'] > 0:
            severity_tabs.append("🟡 Medium Severity")
        if summary['low_severity_issues'] > 0:
            severity_tabs.append("🟢 Low Severity")
        
        if severity_tabs:
            tabs = st.tabs(severity_tabs)
            
            tab_index = 0
            for severity, color in [("HIGH", "🔴"), ("MEDIUM", "🟡"), ("LOW", "🟢")]:
                severity_issues = [issue for issue in results['detailed_issues'] if issue['severity'] == severity]
                
                if severity_issues and tab_index < len(tabs):
                    with tabs[tab_index]:
                        display_severity_issues(severity_issues, severity, df)
                    tab_index += 1
    else:
        st.info("🎉 No data quality issues detected! Your dataset appears to be logically consistent.")
    
    # Recommendations section
    if results['recommendations']:
        st.subheader("💡 Recommendations")
        
        for rec_group in results['recommendations']:
            priority_color = {
                'HIGH': '🔴',
                'MEDIUM': '🟡', 
                'LOW': '🟢'
            }
            
            with st.expander(f"{priority_color[rec_group['priority']]} {rec_group['title']}", expanded=rec_group['priority'] == 'HIGH'):
                for i, item in enumerate(rec_group['items'], 1):
                    st.markdown(f"{i}. {item}")
    
    # Export options
    st.subheader("📥 Export Validation Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Download Detailed Report"):
            report_json = json.dumps(results, indent=2, default=str)
            st.download_button(
                label="Download JSON Report",
                data=report_json,
                file_name=f"advanced_validation_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Download Issue Summary"):
            # Create summary DataFrame
            summary_data = []
            for issue in results['detailed_issues']:
                summary_data.append({
                    'Category': issue['category'],
                    'Severity': issue['severity'],
                    'Description': issue['description'],
                    'Affected Records': issue['count'],
                    'Percentage': f"{issue['affected_percentage']}%",
                    'Recommendation': issue['recommendation']
                })
            
            summary_df = pd.DataFrame(summary_data)
            csv = summary_df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV Summary",
                data=csv,
                file_name=f"validation_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

def display_severity_issues(issues: list, severity: str, df: pd.DataFrame):
    """Display issues for a specific severity level"""
    
    for i, issue in enumerate(issues):
        with st.container():
            # Issue header
            st.markdown(f"### {i+1}. {issue['category']}")
            
            # Issue details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Description:** {issue['description']}")
                st.markdown(f"**Recommendation:** {issue['recommendation']}")
            
            with col2:
                st.metric("Affected Records", issue['count'])
                st.metric("Percentage", f"{issue['affected_percentage']}%")
            
            # Examples section
            if issue['examples']:
                with st.expander(f"📋 View Examples ({len(issue['examples'])} shown)", expanded=False):
                    
                    # Handle different example formats
                    if isinstance(issue['examples'][0], dict):
                        if 'email' in issue['examples'][0]:
                            # Email duplicate examples
                            for example in issue['examples']:
                                st.markdown(f"**Email:** `{example['email']}` (appears {example['count']} times)")
                                if 'records' in example:
                                    example_df = pd.DataFrame(example['records'])
                                    st.dataframe(example_df, use_container_width=True)
                        
                        elif 'normalized_phone' in issue['examples'][0]:
                            # Phone duplicate examples
                            for example in issue['examples']:
                                st.markdown(f"**Phone:** `{example['normalized_phone']}` (appears {example['count']} times)")
                                if 'records' in example:
                                    example_df = pd.DataFrame(example['records'])
                                    st.dataframe(example_df, use_container_width=True)
                        
                        elif 'period' in issue['examples'][0]:
                            # Bulk import pattern examples
                            for example in issue['examples']:
                                st.markdown(f"**Period:** {example['period']} ({example['count']} records, {example['percentage_of_total']}% of total)")
                                if 'sample_records' in example:
                                    example_df = pd.DataFrame(example['sample_records'])
                                    st.dataframe(example_df, use_container_width=True)
                        
                        else:
                            # Generic examples
                            for j, example in enumerate(issue['examples']):
                                st.markdown(f"**Example {j+1}:**")
                                st.json(example)
                    
                    else:
                        # Simple list examples
                        example_df = pd.DataFrame(issue['examples'])
                        st.dataframe(example_df, use_container_width=True)
            
            st.markdown("---")

def create_validation_visualization(results: Dict[str, Any]) -> go.Figure:
    """Create comprehensive validation visualization"""
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Issues by Severity', 'Affected Records Distribution', 
                       'Data Quality Score', 'Issue Categories'),
        specs=[[{"type": "bar"}, {"type": "pie"}],
               [{"type": "indicator"}, {"type": "bar"}]]
    )
    
    summary = results['summary']
    
    # Severity distribution
    fig.add_trace(
        go.Bar(
            x=['High', 'Medium', 'Low'],
            y=[summary['high_severity_issues'], summary['medium_severity_issues'], summary['low_severity_issues']],
            marker_color=['#FF4B4B', '#FFA500', '#32CD32'],
            name='Issues by Severity'
        ),
        row=1, col=1
    )
    
    # Affected vs Clean records
    affected = summary['total_affected_records']
    clean = summary['total_records'] - affected
    
    fig.add_trace(
        go.Pie(
            labels=['Clean Records', 'Affected Records'],
            values=[clean, affected],
            marker_colors=['#32CD32', '#FF4B4B'],
            name='Record Distribution'
        ),
        row=1, col=2
    )
    
    # Data Quality Score
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=summary['data_quality_score'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Data Quality Score"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=2, col=1
    )
    
    # Issue categories
    if results['detailed_issues']:
        categories = [issue['category'] for issue in results['detailed_issues']]
        counts = [issue['count'] for issue in results['detailed_issues']]
        
        fig.add_trace(
            go.Bar(
                x=categories,
                y=counts,
                marker_color='#1f77b4',
                name='Issues by Category'
            ),
            row=2, col=2
        )
    
    fig.update_layout(height=800, showlegend=False, title_text="Advanced Data Quality Validation Dashboard")
    
    return fig
