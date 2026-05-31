# Evidence Basket Usage Guide

## Overview

The Evidence Basket allows you to select specific log entries from search or cluster results and send them to the AI diagnosis system for analysis. This is useful when you want to diagnose a specific subset of errors rather than all results.

## Workflow

```
Search/Cluster Results → Select Items → Add to Basket → Diagnose → View Results
```

## Using the Evidence Basket

### 1. Search or Cluster Your Logs

First, perform a log search or cluster analysis as usual:

- **Search**: Enter keywords and filters, then click "Search"
- **Cluster**: Select a directory and click "Start Clustering"

### 2. Select Items

When results are displayed, you'll see checkboxes for selecting individual items:

**In Search Results:**
- Individual log entries have checkboxes on the left
- Each group (aggregated results) has a "Select All" option
- You can select specific entries or entire groups

**In Cluster Results:**
- Expand a cluster group by clicking "展开"
- Individual log entries within the expanded view have checkboxes
- The cluster itself can be selected (selects all its log entries)

### 3. View Your Selection

The Evidence Basket icon in the header shows a badge with the count of selected items:

- Click the basket icon to open the drawer
- Review your selected items before diagnosis
- Remove individual items or clear all

### 4. Send to Diagnosis

Click the "AI 诊断" (AI Diagnosis) button in the Evidence Basket drawer:

1. The system compresses your selected evidence
2. Sends it to the LLM with context
3. Returns a diagnosis in a new drawer

### 5. Review Diagnosis Results

The diagnosis result appears in a right-side drawer containing:

- **Summary**: Quick overview of the issue
- **Root Cause**: AI's analysis of the underlying cause
- **Suggestions**: Recommended actions

## Compression Options

Before sending for diagnosis, you can configure:

| Option | Default | Description |
|--------|---------|-------------|
| Include Stack Traces | On | Include stack trace information |
| Include Timeline | On | Include time distribution analysis |
| Max Tokens | 2000 | Token budget for evidence (100-10000) |

## Selection Types

When selecting items for diagnosis, the system supports:

| Type | Description | Use Case |
|------|-------------|----------|
| `log` | Single log entry | Specific error you want to investigate |
| `group` | All entries in a group | Same type of error from search results |
| `group_all` | All entries in all groups | Full search result set |
| `cluster` | All entries in a cluster | Anomaly pattern from clustering |

## How Evidence is Processed

1. **Deduplication**: Duplicate log entries (same file, line, timestamp) are removed
2. **Compression**: Evidence is summarized with statistics (count, time range, peak window)
3. **Token Budget**: Large selections are truncated to fit within the max_tokens limit
4. **LLM Analysis**: The compressed evidence is sent to the configured LLM

## Viewing Matched Lines in Clusters

For cluster results:

1. Click "展开" (Expand) on a cluster group
2. The matched log entries are loaded from cache
3. You can select individual entries or the entire cluster
4. Selected items show in the Evidence Basket

Note: The displayed entry count may be less than the total error count due to deduplication.

## Tips

- **Be specific**: Select only relevant entries for more accurate diagnosis
- **Check compression**: Large selections may be truncated - consider using filters first
- **Review context**: The system includes 5 lines of context before/after each log entry
- **Multiple diagnoses**: You can run multiple diagnoses with different selections

## Troubleshooting

### "No search cache available" Error

This occurs when trying to diagnose cluster results without matched lines cached. The cluster analysis must complete successfully and store matched lines.

### Duplicate Selection

If selecting one item selects multiple, this may be due to duplicate entries in the cache with the same ID. The system now deduplicates these automatically.

### Diagnosis Timeout

Large evidence sets may take longer. Try:
- Reducing the number of selected items
- Lowering the max_tokens setting
- Enabling only essential compression options
