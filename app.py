import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import json
from datetime import datetime

# Import our modules
from data_processor import DataProcessor
from cleaning_engine import CleaningEngine
from config import Config
from utils.logger import setup_logger
from advanced_validation_ui import render_advanced_validation_tab

# Configure page
st.set_page_config(
    page_title="AI-Based Data Cleaner",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logger
logger = setup_logger(__name__)

# Initialize session state
if 'original_df' not in st.session_state:
    st.session_state.original_df = None
if 'cleaned_df' not in st.session_state:
    st.session_state.cleaned_df = None
if 'cleaning_report' not in st.session_state:
    st.session_state.cleaning_report = None
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False

def main():
    """Main application function"""
    
    # Header
    st.title("🧹 AI-Based Data Cleaner")
    st.markdown("Upload your Excel or CSV file and let AI clean your data automatically!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Check API key
        if not Config.OPENAI_API_KEY:
            st.error("⚠️ OpenAI API key not found! Please set OPENAI_API_KEY in your .env file.")
            st.stop()
        else:
            st.success("✅ OpenAI API key configured")
        
        st.header("🔧 Cleaning Options")
        cleaning_options = {
            'remove_duplicates': st.checkbox("Remove duplicate rows", value=True),
            'ai_text_cleaning': st.checkbox("AI-powered text cleaning", value=True),
            'fill_missing_values': st.checkbox("Fill missing values", value=True),
            'use_ai_for_missing': st.checkbox("Use AI for missing values (small datasets)", value=False),
            'fix_data_types': st.checkbox("Fix data types", value=True),
            'handle_outliers': st.checkbox("Handle outliers", value=False)
        }
        
        if st.button("ℹ️ About"):
            show_about()
    
    # Main content area
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📁 Upload & Clean", "📊 Data Analysis", "🔍 Before/After", "🔬 Advanced Validation", "📥 Download"])
    
    with tab1:
        upload_and_clean_tab(cleaning_options)
    
    with tab2:
        data_analysis_tab()
    
    with tab3:
        before_after_tab()
    
    with tab4:
        advanced_validation_tab()

    with tab5:
        download_tab()

def upload_and_clean_tab(cleaning_options):
    """File upload and cleaning tab"""
    
    st.header("📁 Upload Your Data File")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help=f"Maximum file size: {Config.MAX_FILE_SIZE_MB}MB"
    )
    
    if uploaded_file is not None:
        try:
            # Check file size
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > Config.MAX_FILE_SIZE_MB:
                st.error(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({Config.MAX_FILE_SIZE_MB}MB)")
                return
            
            # Load data
            with st.spinner("Loading data..."):
                data_processor = DataProcessor()
                df = data_processor.read_file(uploaded_file.getvalue(), uploaded_file.name)
                st.session_state.original_df = df
                st.session_state.file_uploaded = True
            
            st.success(f"✅ File loaded successfully! Shape: {df.shape}")
            
            # Show data preview
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Data quality overview
            st.subheader("📈 Data Quality Overview")
            show_data_quality_overview(df)
            
            # Clean data button
            if st.button("🧹 Clean Data", type="primary", use_container_width=True):
                clean_data(df, cleaning_options)
                
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            logger.error(f"Error loading file {uploaded_file.name}: {str(e)}")

def clean_data(df, cleaning_options):
    """Clean the data using the cleaning engine"""
    
    try:
        with st.spinner("🤖 AI is cleaning your data... This may take a few minutes."):
            # Initialize cleaning engine
            cleaning_engine = CleaningEngine()
            
            # Clean the data
            cleaned_df, cleaning_report = cleaning_engine.clean_dataset(df, cleaning_options)
            
            # Store results in session state
            st.session_state.cleaned_df = cleaned_df
            st.session_state.cleaning_report = cleaning_report
        
        st.success("✅ Data cleaning completed!")
        
        # Show summary
        if cleaning_report['statistics'].get('summary'):
            summary = cleaning_report['statistics']['summary']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Changes", summary['total_changes'])
            with col2:
                st.metric("Missing Values", 
                         f"{summary['missing_values_after']}", 
                         f"-{summary['missing_values_before'] - summary['missing_values_after']}")
            with col3:
                st.metric("Rows", summary['rows_after'], 
                         f"{summary['rows_after'] - summary['rows_before']}")
            with col4:
                st.metric("Missing Reduction", f"{summary['missing_reduction_percentage']:.1f}%")
        
        # Show errors if any
        if cleaning_report.get('errors'):
            st.warning("⚠️ Some issues occurred during cleaning:")
            for error in cleaning_report['errors']:
                st.write(f"• {error}")
                
    except Exception as e:
        st.error(f"Error during data cleaning: {str(e)}")
        logger.error(f"Error during data cleaning: {str(e)}")

def show_data_quality_overview(df):
    """Show data quality overview"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Rows", f"{df.shape[0]:,}")
    with col2:
        st.metric("Columns", df.shape[1])
    with col3:
        missing_count = df.isnull().sum().sum()
        st.metric("Missing Values", f"{missing_count:,}")
    with col4:
        duplicate_count = df.duplicated().sum()
        st.metric("Duplicates", f"{duplicate_count:,}")
    
    # Missing values by column
    if missing_count > 0:
        st.subheader("Missing Values by Column")
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
        
        if len(missing_data) > 0:
            fig = px.bar(
                x=missing_data.values,
                y=missing_data.index,
                orientation='h',
                title="Missing Values Count by Column"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def data_analysis_tab():
    """Data analysis and statistics tab"""
    
    if st.session_state.original_df is None:
        st.info("Please upload a file first.")
        return
    
    st.header("📊 Data Analysis")
    
    df = st.session_state.original_df
    
    # Column selection
    selected_columns = st.multiselect(
        "Select columns to analyze:",
        df.columns.tolist(),
        default=df.columns.tolist()[:5]
    )
    
    if selected_columns:
        # Basic statistics
        st.subheader("📈 Basic Statistics")
        st.dataframe(df[selected_columns].describe(), use_container_width=True)
        
        # Data types
        st.subheader("🏷️ Data Types")
        dtype_df = pd.DataFrame({
            'Column': selected_columns,
            'Data Type': [str(df[col].dtype) for col in selected_columns],
            'Non-Null Count': [df[col].count() for col in selected_columns],
            'Unique Values': [df[col].nunique() for col in selected_columns]
        })
        st.dataframe(dtype_df, use_container_width=True)

def before_after_tab():
    """Before/after comparison tab"""
    
    if st.session_state.original_df is None or st.session_state.cleaned_df is None:
        st.info("Please upload and clean a file first.")
        return
    
    st.header("🔍 Before/After Comparison")
    
    original_df = st.session_state.original_df
    cleaned_df = st.session_state.cleaned_df
    
    # Column selection for comparison
    column = st.selectbox("Select column to compare:", original_df.columns)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Before Cleaning")
        st.dataframe(original_df[column].head(20), use_container_width=True)
        
        # Statistics
        if original_df[column].dtype in ['int64', 'float64']:
            st.write("**Statistics:**")
            st.write(f"Mean: {original_df[column].mean():.2f}")
            st.write(f"Missing: {original_df[column].isnull().sum()}")
    
    with col2:
        st.subheader("✨ After Cleaning")
        st.dataframe(cleaned_df[column].head(20), use_container_width=True)
        
        # Statistics
        if cleaned_df[column].dtype in ['int64', 'float64']:
            st.write("**Statistics:**")
            st.write(f"Mean: {cleaned_df[column].mean():.2f}")
            st.write(f"Missing: {cleaned_df[column].isnull().sum()}")
    
    # Show changes made
    if st.session_state.cleaning_report:
        st.subheader("📝 Changes Made")
        changes = st.session_state.cleaning_report.get('changes', [])
        column_changes = [change for change in changes if change.get('column') == column]
        
        if column_changes:
            for change in column_changes:
                st.write(f"• **{change['type']}**: {change}")
        else:
            st.info("No changes made to this column.")

def download_tab():
    """Download cleaned data tab"""
    
    if st.session_state.cleaned_df is None:
        st.info("Please clean your data first.")
        return
    
    st.header("📥 Download Cleaned Data")
    
    cleaned_df = st.session_state.cleaned_df
    
    # File format selection
    file_format = st.radio("Select download format:", ["CSV", "Excel"])
    
    # Generate download
    if file_format == "CSV":
        csv_buffer = BytesIO()
        cleaned_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    else:  # Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            cleaned_df.to_excel(writer, sheet_name='Cleaned_Data', index=False)
            
            # Add cleaning report if available
            if st.session_state.cleaning_report:
                report_df = pd.DataFrame(st.session_state.cleaning_report['changes'])
                if not report_df.empty:
                    report_df.to_excel(writer, sheet_name='Cleaning_Report', index=False)
        
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # Show cleaning report
    if st.session_state.cleaning_report:
        st.subheader("📋 Cleaning Report")
        
        with st.expander("View detailed cleaning report"):
            st.json(st.session_state.cleaning_report)

def advanced_validation_tab():
    """Advanced data quality validation tab"""
    if st.session_state.original_df is not None:
        render_advanced_validation_tab(st.session_state.original_df)
    else:
        st.info("📁 Please upload a data file first to perform advanced validation.")
        st.markdown("""
        ### 🔬 Advanced Data Quality Validation

        This feature provides comprehensive analysis of your data for:

        - **🔍 Duplicate Identity Detection**: Find duplicate emails, phone numbers, and contact information
        - **📊 Data Pattern Anomalies**: Detect suspicious clustering and artificial standardization
        - **⚖️ Business Logic Violations**: Identify chronological inconsistencies and employment logic errors
        - **🎯 Contextual Integrity Issues**: Spot bulk import patterns and unrealistic data ranges

        Upload your data file to get started!
        """)

def show_about():
    """Show about information"""
    st.info("""
    **AI-Based Data Cleaner** 🧹

    This application uses artificial intelligence to automatically clean and validate your data:

    **Features:**
    • 🤖 AI-powered text cleaning and spelling correction
    • 📊 Intelligent missing value imputation
    • 🔍 Duplicate detection and removal
    • 📈 Data type optimization
    • 📉 Outlier detection and handling

    **Supported Formats:**
    • CSV files (.csv)
    • Excel files (.xlsx, .xls)

    **Requirements:**
    • OpenAI API key for AI features
    • Maximum file size: 50MB
    """)

if __name__ == "__main__":
    main()
