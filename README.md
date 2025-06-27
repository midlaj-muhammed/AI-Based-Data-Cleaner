# 🧹 AI-Based Data Cleaner

A powerful web application that uses artificial intelligence to automatically clean and validate your Excel and CSV files. Built with Python, Streamlit, and OpenAI's GPT API.

## ✨ Features

- **🤖 AI-Powered Text Cleaning**: Automatically fix spelling errors, standardize capitalization, and clean text data
- **📊 Intelligent Missing Value Imputation**: Smart strategies for filling missing data using statistical methods and AI suggestions
- **🔍 Duplicate Detection**: Identify and remove duplicate rows
- **📈 Data Type Optimization**: Automatically detect and convert to optimal data types
- **📉 Outlier Detection**: Identify and handle statistical outliers
- **📋 Comprehensive Reporting**: Detailed before/after analysis with change tracking
- **💾 Multiple Export Formats**: Download cleaned data as CSV or Excel with cleaning reports

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for AI features)

### Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd Ai_Based_Data_Cleaner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** and navigate to `http://localhost:8501`

## 📖 Usage Guide

### 1. Upload Your Data
- Click "Choose a CSV or Excel file" to upload your data
- Supported formats: `.csv`, `.xlsx`, `.xls`
- Maximum file size: 50MB

### 2. Configure Cleaning Options
Use the sidebar to select which cleaning operations to perform:
- **Remove duplicate rows**: Eliminate exact duplicate entries
- **AI-powered text cleaning**: Use AI to fix spelling and formatting
- **Fill missing values**: Intelligent imputation strategies
- **Use AI for missing values**: AI suggestions for small datasets
- **Fix data types**: Optimize column data types
- **Handle outliers**: Cap or remove statistical outliers

### 3. Clean Your Data
- Click "🧹 Clean Data" to start the cleaning process
- Monitor progress and view real-time statistics
- Review the cleaning summary and any warnings

### 4. Analyze Results
- **Data Analysis Tab**: View statistics and data type information
- **Before/After Tab**: Compare original vs. cleaned data column by column
- **Download Tab**: Export cleaned data and cleaning reports

### 5. Download Results
- Choose between CSV or Excel format
- Excel downloads include a separate cleaning report sheet
- Files are timestamped for easy organization

## 🏗️ Project Structure

```
Ai_Based_Data_Cleaner/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration management
├── data_processor.py     # Core data processing functions
├── ai_cleaner.py         # AI-powered cleaning logic
├── cleaning_engine.py    # Main cleaning orchestrator
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── README.md            # This file
├── utils/
│   ├── __init__.py
│   ├── logger.py        # Logging utilities
│   ├── validators.py    # Data validation functions
│   └── error_handler.py # Error handling and reporting
├── examples/
│   ├── sample_data.csv  # Example CSV file
│   └── sample_data.xlsx # Example Excel file
└── logs/                # Application logs
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | - | Yes |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | 50 | No |
| `SUPPORTED_FORMATS` | Comma-separated file formats | csv,xlsx,xls | No |
| `LOG_LEVEL` | Logging level | INFO | No |

### AI Model Configuration

The application uses GPT-3.5-turbo by default. You can modify these settings in `config.py`:

- `OPENAI_MODEL`: AI model to use
- `MAX_TOKENS`: Maximum tokens per API call
- `TEMPERATURE`: AI creativity level (0.0-1.0)

## 🧪 Example Data

The `examples/` directory contains sample files to test the application:

- `sample_data.csv`: CSV file with various data quality issues
- `sample_data.xlsx`: Excel file with multiple sheets and data problems

## 📊 Data Quality Metrics

The application provides comprehensive data quality analysis:

- **Completeness**: Percentage of non-missing values
- **Consistency**: Data type and format consistency
- **Validity**: Adherence to expected patterns and ranges
- **Uniqueness**: Duplicate detection and removal
- **Overall Quality Score**: Weighted combination of all metrics

## 🔍 AI Cleaning Features

### Text Cleaning
- Spelling error correction
- Capitalization standardization
- Whitespace normalization
- Common typo fixes

### Missing Value Imputation
- **Numeric data**: Mean/median based on variance
- **Categorical data**: Mode (most frequent value)
- **AI suggestions**: Context-aware value suggestions for small datasets

### Pattern Detection
- Email validation
- Phone number formatting
- URL validation
- Date format standardization

## 🚨 Error Handling

The application includes comprehensive error handling:

- **File Processing Errors**: Invalid formats, corrupted files
- **AI Service Errors**: API failures, rate limits
- **Data Validation Errors**: Invalid data structures
- **Configuration Errors**: Missing API keys, invalid settings

All errors are logged and presented with user-friendly messages and suggestions.

## 📈 Performance Considerations

- **Large Files**: Files over 1MB may take longer to process
- **AI Features**: Limited to datasets with <1000 unique text values per column
- **Memory Usage**: Large datasets may require significant RAM
- **API Limits**: OpenAI API rate limits may affect processing speed

## 🔒 Security & Privacy

- **Data Privacy**: Your data is processed locally and only sent to OpenAI for AI features
- **API Security**: API keys are stored in environment variables
- **No Data Storage**: The application doesn't store your data permanently
- **Secure Processing**: All file processing happens in memory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Verify your OpenAI API key is valid
3. Ensure your data file is not corrupted
4. Try with a smaller dataset first
5. Check the GitHub issues page for known problems

## 🔄 Version History

- **v1.0.0**: Initial release with core cleaning features
- AI-powered text cleaning
- Statistical missing value imputation
- Comprehensive data validation
- Streamlit web interface

---

**Made with ❤️ using Python, Streamlit, and OpenAI**
# AI-Based-Data-Cleaner
