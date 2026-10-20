# Multi-Agent Research System Benchmark Report

**Generated:** 2026-06-22 07:58:02 UTC

**Duration:** 36.16s


---

## System Information

| Property | Value |
| :--- | :--- |
| Python Version | 3.14.4 |
| Platform | Windows-11-10.0.26200-SP0 |
| CPU Count | 8 |
| Processor | Intel64 Family 6 Model 140 Stepping 1, GenuineIntel |
| Total RAM | 15.79 GB |
| Available RAM | 2.8 GB |

---

## 1. Document Ranking & Text Chunking

**Metrics:** TF-IDF cosine similarity ranking speed and text chunking throughput.

### 1.1 Text Chunking Throughput

| Chunk Size | Overlap | Chunks | Avg Time | Throughput |
| :--- | :--- | :--- | :--- | :--- |
| 250 chars | 25 chars | 16 | 11.0us | 325,791,691 chars/s |
| 500 chars | 50 chars | 8 | 8.0us | 458,598,464 chars/s |
| 1000 chars | 100 chars | 4 | 5.0us | 723,618,506 chars/s |
| 2000 chars | 200 chars | 2 | 3.0us | 1,111,112,631 chars/s |
| 4000 chars | 400 chars | 1 | 2.0us | 2,360,655,783 chars/s |

### 1.2 Ranking Speed (by document count)

| Documents | Avg Time | Std Dev | Top Result |
| :--- | :--- | :--- | :--- |
| 5 | 3.89ms | +/-971.0us | `2305.33333` |
| 10 | 8.92ms | +/-1.91ms | `2305.33333` |
| 25 | 20.03ms | +/-1.37ms | `2305.33333` |
| 50 | 42.75ms | +/-4.70ms | `2305.33333` |
| 100 | 84.41ms | +/-8.40ms | `2305.33333` |

### 1.3 Ranking Accuracy

Query: `quantum computing artificial intelligence`

| Rank | Source | Content Preview |
| :--- | :--- | :--- |
| 1 | `2302.67890` | Trapped ion quantum computers offer unique advantages for qu |
| 2 | `2304.22222` | Quantum error correction is essential for scalable quantum c |
| 3 | `2303.11111` | Topological quantum computing offers a path to fault-toleran |
| 4 | `2309.77777` | We present a comprehensive benchmarking framework for near-t |
| 5 | `2310.88888` | Quantum algorithms for optimization problems offer potential |
| 6 | `2308.66666` | Quantum simulation of many-body systems represents one of th |
| 7 | `2305.33333` | Quantum machine learning algorithms promise computational ad |
| 8 | `2307.55555` | Variational quantum algorithms are promising candidates for  |
| 9 | `2306.44444` | Quantum key distribution enables secure communication with i |
| 10 | `2301.12345` | We demonstrate a superconducting qubit processor with 127 qu |

---

## 2. Citation Validation & Factual Consistency

**Metrics:** Speed of citation validation and numerical claim verification.

### 2.1 Citation Validation Speed

| Documents | Citations in Draft | Invalid Found | Avg Time | Std Dev |
| :--- | :--- | :--- | :--- | :--- |
| 10 | 15 | 10 | 50.6us | +/-83.6us |
| 20 | 25 | 10 | 38.9us | +/-6.0us |
| 50 | 40 | 10 | 55.9us | +/-12.2us |
| 100 | 85 | 10 | 52.8us | +/-3.2us |

### 2.2 Factual Consistency Speed

| Documents | Claims | Unverified Found | Avg Time | Std Dev |
| :--- | :--- | :--- | :--- | :--- |
| 10 | 5 | 3 | 92.2us | +/-80.8us |
| 20 | 20 | 17 | 256.0us | +/-99.9us |
| 50 | 50 | 59 | 3.12ms | +/-670.1us |
| 100 | 100 | 132 | 10.09ms | +/-2.25ms |

### 2.3 Edge Case Performance

| Test Case | Avg Time |
| :--- | :--- |
| Empty Draft Citations Ms | 3.5us |
| Empty Docs Citations Ms | 10.9us |
| No Citations Draft Ms | 10.1us |

---

## 3. Summarization & Timeline Extraction

**Metrics:** Executive brief generation and timeline extraction performance.

### 3.1 Executive Brief Generation

| Report Size | Brief Size | Compression Ratio | Avg Time | Std Dev |
| :--- | :--- | :--- | :--- | :--- |
| 500 chars | 509 chars | 101.8% | 9.0us | +/-6.0us |
| 1,000 chars | 1,008 chars | 100.8% | 14.0us | +/-3.0us |
| 5,000 chars | 2,411 chars | 48.2% | 43.0us | +/-9.0us |
| 10,000 chars | 2,411 chars | 24.1% | 50.0us | +/-25.0us |
| 50,000 chars | 2,929 chars | 5.9% | 448.0us | +/-156.0us |

### 3.2 Timeline Extraction

| Scenario | Avg Time | Entries |
| :--- | :--- | :--- |
| Report Only | 820.0us (+/-164.0us) | 4 |
| Report Only Std | 164.0us (+/-0.0us) | N/A |
| Sources Only | 51.0us (+/-61.0us) | 6 |
| Sources Only Std | 61.0us (+/-0.0us) | N/A |
| Combined | 539.0us (+/-182.0us) | 7 |
| Combined Std | 182.0us (+/-0.0us) | N/A |
| Many Sources 200 | 1.47ms (+/-658.0us) | 6 |
| Many Sources 200 Std | 658.0us (+/-0.0us) | N/A |

### 3.3 Edge Cases

| Test Case | Avg Time |
| :--- | :--- |
| Empty Report Ms | 1.6us |
| Tiny Report Ms | 2.5us |
| Large Report 100X Ms | 7.47ms |

---

## 4. Chat Prompt Construction

**Metrics:** Follow-up chat prompt building speed.

### 4.1 Prompt Construction Speed (by source count)

| Sources | Avg Time | Std Dev |
| :--- | :--- | :--- |
| 0 | 7.7us | +/-0.7us |
| 5 | 7.2us | +/-4.8us |
| 10 | 7.3us | +/-1.2us |
| 20 | 19.5us | +/-6.4us |
| 50 | 20.7us | +/-4.8us |
| 100 | 19.0us | +/-0.8us |

### 4.2 Content Verification

| Check | Status |
| :--- | :--- |
| Contains Report | PASS |
| Contains Question | PASS |
| Contains Source | PASS |
| Contains Answer Marker | PASS |
| Contains Formatting Instructions | PASS |
| Contains Role Instruction | PASS |
| Contains Citation Instruction | PASS |

---

## 5. DOI Resolution (arXiv ID Extraction)

**Metrics:** arXiv ID extraction speed and pattern support.

### 5.1 Extraction Speed

| URLs Processed | IDs Found | Extraction Ratio | Avg Time | Throughput |
| :--- | :--- | :--- | :--- | :--- |
| 10 | 8 | 80% | 22.4us | 447,160 urls/s |
| 50 | 40 | 80% | 94.0us | 531,858 urls/s |
| 100 | 80 | 80% | 172.8us | 578,759 urls/s |
| 500 | 400 | 80% | 898.6us | 556,410 urls/s |
| 1,000 | 800 | 80% | 2.77ms | 360,964 urls/s |
| 5,000 | 4,000 | 80% | 11.82ms | 423,028 urls/s |

### 5.2 URL Pattern Support

| Pattern | Input -> Output | Avg Time |
| :--- | :--- | :--- |
| abs URL | 1 -> 1 IDs | 3.1us |
| pdf URL | 1 -> 1 IDs | 3.0us |
| versioned URL | 1 -> 1 IDs | 2.9us |
| HTTPS abs | 1 -> 1 IDs | 3.1us |
| case insensitive | 1 -> 1 IDs | 3.2us |
| query params | 1 -> 1 IDs | 2.7us |
| mixed batch | 4 -> 3 IDs | 10.6us |
| non-arxiv only | 2 -> 0 IDs | 3.2us |
| empty list | 0 -> 0 IDs | 0.6us |

---

## 6. Image Search Cache & Search Latency

**Metrics:** Cache operations, query normalization, DDGS image/graph search latency, cache throughput.

### 6.1 Cache Operations

| Operation | Avg Time |
| :--- | :--- |
| Cache Set 20 Items Ms | 1.0us |
| Cache Get Hit Ms | 0.8us |
| Cache Get Miss Ms | 0.7us |
| Cache Clear Ms | 94.8us |

### 6.2 Query Normalization

| Input Length | Normalized | Avg Time |
| :--- | :--- | :--- |
| 26 chars | `quantum computing research` | 1.2us |
| 32 chars | `quantum  computing  research` | 0.9us |
| 30 chars | `quantum computing research!@#$` | 0.9us |
| 60 chars | `what is the impact of quantum computing ` | 1.1us |
| 87 chars | `a very long query about quantum computin` | 0.8us |

### 6.3 DDGS Search Latency (network-dependent)

| Metric | Value |
| :--- | :--- |
| Image Search Cold Avg S | 1.273 |
| Image Search Cold Std S | 0.728 |
| Image Search Cold Min S | 0.487 |
| Image Search Cold Max S | 1.925 |
| Image Search Warm Avg Ms | 0.125 |
| Image Search Warm Std Ms | 0.017 |
| Graph Search Cold Avg S | 1.026 |
| Graph Search Cold Std S | 0.376 |
| Cache Acceleration Ratio | 10184.0 |

### 6.4 Cache-Accelerated Throughput

| Metric | Value |
| :--- | :--- |
| Cache Throughput 50 Runs Ms | 0.1379 |
| Cache Throughput 50 Runs Total S | 0.0069 |

---

## 7. Pipeline & State Management

**Metrics:** State construction, graph generation, response serialization.

### 7.1 Agent State Construction

| State Type | Avg Time |
| :--- | :--- |
| Basic State Ms | 37.9us |
| Full State Ms | 106.0us |

### 7.2 Knowledge Graph Construction

| Documents | Nodes | Links | Avg Time |
| :--- | :--- | :--- | :--- |
| 0 | 0 | 0 | 110.0us |
| 100 | 100 | 0 | 89.45ms |
| 10 | 10 | 0 | 4.51ms |
| 25 | 25 | 0 | 14.50ms |
| 50 | 50 | 0 | 40.30ms |
| 5 | 5 | 0 | 2.57ms |

### 7.3 Research Response Construction

| Sources | Avg Time |
| :--- | :--- |
| 5 | 98.3us |
| 20 | 100.5us |
| 50 | 204.5us |
| 100 | 183.4us |

### 7.4 Serialization Performance

| Operation | Avg Time |
| :--- | :--- |
| Model Dump Ms | 61.7us |
| Json Serialize Ms | 181.8us |
| Full Serialization Ms | 333.1us |
| JSON Output Size | 14,091 bytes (13.8 KB) |

---

## 8. PDF Upload Handling & Text Extraction

**Metrics:** PDF text extraction, validation density, reference stripping, column detection.

### 8.1 PDF Text Extraction Speed

| Pages | PDF Size | Extracted Chars | Avg Time | Throughput |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 8,382 bytes | 2,595 chars | 11.02ms | 90.7 pages/s |
| 3 | 21,887 bytes | 7,302 chars | 19.54ms | 153.5 pages/s |
| 5 | 35,448 bytes | 12,002 chars | 23.96ms | 208.7 pages/s |
| 10 | 69,444 bytes | 23,764 chars | 57.38ms | 174.3 pages/s |
| 20 | 137,435 bytes | 25,878 chars | 68.75ms | 290.9 pages/s |
| 50 | 341,927 bytes | 25,878 chars | 54.79ms | 912.5 pages/s |

### 8.2 Text Segment Validation

| Test Case | Avg Time |
| :--- | :--- |
| Valid Text Density Ms | 75.8us |
| Garbage Text Density Ms | 52.6us |
| Short Text Under 50 Chars Ms | 0.2us |
| Empty Text Ms | 0.2us |

### 8.3 Reference Section Stripping

| Scenario | Input -> Output | Avg Time |
| :--- | :--- | :--- |
| no_references | 3,050 -> 3,022 chars | 192.1us |
| with_references | 1,989 -> 1,899 chars | 141.1us |
| large_document | 27,687 -> 24,499 chars | 1.06ms |
| early_references_kept | 1,675 -> 1,638 chars | 74.5us |

### 8.4 Column Layout Detection

| Layout | Avg Time |
| :--- | :--- |
| Two Column Detection Ms | 0.6us |
| Single Column Empty Right Ms | 0.3us |
| Imbalanced Columns Ms | 0.6us |
| Both Empty Ms | 0.3us |

### 8.5 Individual Page Extraction

- **Avg Time:** 160.0us +/-58.0us
- **Extracted Text:** 113 chars

---

## Performance Summary

| Benchmark | Best Case | Worst Case |
| :--- | :--- | :--- |
| Text Chunking (250-4000 chars) | 2.0us | 11.0us |
| Citation Validation | 38.9us | 55.9us |
| Executive Brief Generation | 9.0us | 448.0us |
| arXiv ID Extraction | 22.4us | 11.82ms |
| PDF Text Extraction (1-50 pages) | 11.02ms | 68.75ms |
| Image Search Cache Acceleration | 10184.0x faster | - |

---

*Report generated by Multi-Agent Research System Benchmark Suite v0.2.0*
