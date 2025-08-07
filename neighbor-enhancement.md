# 🚀 Enhanced Search with Neighboring Chunks

## New Feature: Context-Aware Retrieval

PolicyPilot now includes **neighboring chunk retrieval** to provide better context and more comprehensive results!

### How It Works

When PolicyPilot finds a relevant chunk in your documents (e.g., at index 15), it now automatically includes:
- **Previous chunk** (index 14) 
- **Next chunk** (index 16)
- This provides better context around the matched content

### Benefits

✅ **Better Context**: Get the full picture around relevant sections  
✅ **Improved Accuracy**: Related information that might be split across chunks  
✅ **Enhanced Understanding**: See before/after content for complete comprehension  

### Configuration

#### Backend API Parameters

```json
{
  "query": "What are the exclusions?",
  "include_neighbors": true,
  "neighbor_range": 1
}
```

- `include_neighbors`: Enable/disable neighbor inclusion (default: `true`)
- `neighbor_range`: Number of neighbors on each side (default: `1`, meaning ±1)

#### Examples

**Range = 1** (default): Includes chunks [14, 15, 16] if match found at 15  
**Range = 2**: Includes chunks [13, 14, 15, 16, 17] if match found at 15  
**Range = 0**: Only the matched chunk (original behavior)

### API Endpoints Updated

1. **POST /process** - Main query processing
2. **GET /search/{query}** - Direct document search

Both endpoints now support:
- `include_neighbors` (query param/body param)
- `neighbor_range` (query param/body param)

### Frontend Integration

The React frontend automatically uses the enhanced search with:
```javascript
{
  query: "your question",
  include_neighbors: true,
  neighbor_range: 1
}
```

### Performance Impact

- **Minimal overhead**: Neighbor lookup is efficient using chunk ID indexing
- **Smart deduplication**: Prevents duplicate chunks in results
- **Score adjustment**: Neighboring chunks get 80% of original match score

### Configuration Files

Update `backend/config.py`:
```python
# Retrieval
INCLUDE_NEIGHBORS: bool = True
NEIGHBOR_RANGE: int = 1
```

### Use Cases

**Medical Claims**: Find complete treatment descriptions that span multiple chunks  
**Policy Terms**: Get full context of conditions and exclusions  
**Procedures**: See complete step-by-step instructions  

---

🎯 **Result**: More accurate, context-aware responses with comprehensive information retrieval!
