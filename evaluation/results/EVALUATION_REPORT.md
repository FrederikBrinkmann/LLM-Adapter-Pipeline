# LLM Evaluation Report
Generated: 2026-01-26 16:40:52
Total Test Runs: 14

## Overview

This report evaluates different LLM models and prompts on their ability to extract
structured insurance claim data from unstructured emails.

### Metrics Explained

- **Accuracy**: Percentage of critical fields correctly extracted
- **Schema Valid**: Output matches the required JSON schema
- **Critical Fields**: Correct identification of has_missing_critical_fields
- **F1 Score**: Balanced metric for missing fields detection (Precision + Recall)

## Model Comparison

| Model | Runs | Avg Accuracy | Avg Time | Critical Fields | Passed |
|-------|------|--------------|----------|-----------------|--------|
| gpt-4.1 | 2 | 87.5% | 5905ms | 0% | 0% |
| gpt-4.1-mini | 2 | 87.5% | 3462ms | 0% | 0% |
| gpt-4o | 2 | 87.5% | 5162ms | 0% | 0% |
| gpt-4o-mini | 2 | 87.5% | 6725ms | 0% | 0% |

## Performance by Difficulty

| Difficulty | Cases | Avg Accuracy | Avg F1 (Missing Fields) |
|------------|-------|--------------|-------------------------|
| Easy       |     4 |        100.0% |                    0.25 |
| Medium     |     4 |         75.0% |                    0.73 |

## Detailed Results

### gpt-4.1 - EASY_001
- **Difficulty**: easy
- **Accuracy**: 100.0%
- **Schema Valid**: ❌
- **Critical Fields**: ❌
- **Missing Fields F1**: 0.00
- **Response Time**: 4968ms

### gpt-4.1 - MEDIUM_001
- **Difficulty**: medium
- **Accuracy**: 75.0%
- **Schema Valid**: ❌
- **Critical Fields**: ❌
- **Missing Fields F1**: 0.75
- **Response Time**: 6842ms

### gpt-4.1-mini - EASY_001
- **Difficulty**: easy
- **Accuracy**: 100.0%
- **Schema Valid**: ❌
- **Critical Fields**: ❌
- **Missing Fields F1**: 0.00
- **Response Time**: 3890ms

### gpt-4.1-mini - MEDIUM_001
- **Difficulty**: medium
- **Accuracy**: 75.0%
- **Schema Valid**: ❌
- **Critical Fields**: ❌
- **Missing Fields F1**: 0.75
- **Response Time**: 3034ms

### gpt-4o - EASY_001
- **Difficulty**: easy
- **Accuracy**: 100.0%
- **Schema Valid**: ❌
- **Critical Fields**: ❌
- **Missing Fields F1**: 0.00
- **Response Time**: 3640ms

### gpt-4o - MEDIUM_001
- **Difficulty**: medium
- **Accuracy**: 75.0%
- **Schema Valid**: ❌
- **Critical Fields**: ❌
- **Missing Fields F1**: 0.75
- **Response Time**: 6685ms

### gpt-4o-mini - EASY_001
- **Difficulty**: easy
- **Accuracy**: 100.0%
- **Schema Valid**: ❌
- **Critical Fields**: ❌
- **Missing Fields F1**: 1.00
- **Response Time**: 7973ms

### gpt-4o-mini - MEDIUM_001
- **Difficulty**: medium
- **Accuracy**: 75.0%
- **Schema Valid**: ❌
- **Critical Fields**: ❌
- **Missing Fields F1**: 0.67
- **Response Time**: 5476ms

### llama3 - EASY_001
❌ Error: LLM call failed: Ollama returned invalid JSON content

### llama3 - MEDIUM_001
❌ Error: LLM call failed: Ollama returned invalid JSON content

### mistral - EASY_001
❌ Error: LLM call failed: Ollama request failed: 404 Not Found: {"error":"model 'mistral' not found"}

### mistral - MEDIUM_001
❌ Error: LLM call failed: Ollama request failed: 404 Not Found: {"error":"model 'mistral' not found"}

### phi3 - EASY_001
❌ Error: LLM call failed: Ollama request failed: 404 Not Found: {"error":"model 'phi3' not found"}

### phi3 - MEDIUM_001
❌ Error: LLM call failed: Ollama request failed: 404 Not Found: {"error":"model 'phi3' not found"}


## Conclusion

This evaluation demonstrates the effectiveness of different LLM models
in extracting structured data from insurance claim emails.

- **Best Model**: Determined by average accuracy across all test cases
- **Difficulty Analysis**: Harder cases show the model's capability with incomplete data
- **Schema Compliance**: All models should produce valid JSON output