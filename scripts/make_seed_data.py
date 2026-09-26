"""Generate deterministic, balanced seed prompts in CSV and JSON formats."""
import csv
import json
import os

PROMPTS = [
    # factual_qa
    {"prompt": "Explain the concept of quantum entanglement in simple terms.", "category": "factual_qa"},
    {"prompt": "What is the time complexity of quicksort in average and worst cases?", "category": "factual_qa"},
    {"prompt": "Why is the sky blue during the day and red during sunset?", "category": "factual_qa"},
    {"prompt": "Explain the difference between HTTP and HTTPS protocols.", "category": "factual_qa"},
    {"prompt": "What are the primary differences between supervised and unsupervised machine learning?", "category": "factual_qa"},
    {"prompt": "What is the purpose and mechanism of a network firewall?", "category": "factual_qa"},
    {"prompt": "What are the core architectural components of a modern operating system kernel?", "category": "factual_qa"},
    {"prompt": "Explain the biological mechanism of photosynthesis in plants.", "category": "factual_qa"},

    # creative_writing
    {"prompt": "Write a short story about an autonomous deep-sea submersible discovering an uncharted hydrothermal vent.", "category": "creative_writing"},
    {"prompt": "Compose a reflective poem about late autumn foliage dissolving into early winter frost.", "category": "creative_writing"},
    {"prompt": "Write an engaging dialogue between an archivist from the 19th century and a quantum computer scientist.", "category": "creative_writing"},
    {"prompt": "Create an opening scene for a neo-noir detective novel set in an orbital space station.", "category": "creative_writing"},
    {"prompt": "Write a poignant micro-fiction about a lighthouse keeper during the final automated decommissioning.", "category": "creative_writing"},
    {"prompt": "Draft a whimsical monologue of an old bookstore cat observing peculiar nighttime patrons.", "category": "creative_writing"},
    {"prompt": "Describe a bustling floating market on a terraformed Martian canal at dusk.", "category": "creative_writing"},
    {"prompt": "Write a suspenseful flash fiction piece about a forgotten satellite transmitting an unexpected signal.", "category": "creative_writing"},

    # code_generation
    {"prompt": "Given a list of numbers, write an efficient Python function to return the median without using external libraries.", "category": "code_generation"},
    {"prompt": "Write a SQL query to identify the top 5 customers by revenue over the past 12 months using window functions.", "category": "code_generation"},
    {"prompt": "Write a Python function to detect whether a given string is a valid palindrome, ignoring punctuation and casing.", "category": "code_generation"},
    {"prompt": "Generate a robust regular expression in Python that validates RFC 5322 standard email addresses.", "category": "code_generation"},
    {"prompt": "Write a thread-safe Singleton pattern implementation in Python using a metaclass.", "category": "code_generation"},
    {"prompt": "Write a TypeScript function that performs deep object cloning without using structuredClone.", "category": "code_generation"},
    {"prompt": "Implement an iterative binary search algorithm in Python that returns the index or -1 if absent.", "category": "code_generation"},
    {"prompt": "Write an asynchronous Python function using httpx to fetch multiple URLs concurrently with rate limiting.", "category": "code_generation"},

    # summarization
    {"prompt": "Summarize the core philosophical arguments of Plato's Allegory of the Cave in three concise sentences.", "category": "summarization"},
    {"prompt": "Provide an executive summary of how renewable energy storage buffers grid intermittency.", "category": "summarization"},
    {"prompt": "Summarize the key events and historical significance of the Industrial Revolution in two paragraphs.", "category": "summarization"},
    {"prompt": "Summarize the differences between monolithic and microservice software architectures for non-technical stakeholders.", "category": "summarization"},
    {"prompt": "Condense the primary findings of the IPCC Climate Assessment Report regarding global temperature anomalies.", "category": "summarization"},
    {"prompt": "Summarize the plot and thematic moral conflict in Shakespeare's Macbeth in under 100 words.", "category": "summarization"},
    {"prompt": "Provide a high-level briefing on the discovery and clinical utility of CRISPR-Cas9 gene editing.", "category": "summarization"},
    {"prompt": "Summarize the psychological principles underlying cognitive dissonance and rationalization.", "category": "summarization"},

    # reasoning
    {"prompt": "Analyze the trade-offs between strong consistency and eventual consistency in distributed systems.", "category": "reasoning"},
    {"prompt": "Evaluate whether carbon offset credits genuinely reduce net greenhouse gas emissions or merely shift liability.", "category": "reasoning"},
    {"prompt": "Explain the CAP theorem and justify which two properties an online banking transaction ledger should prioritize.", "category": "reasoning"},
    {"prompt": "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost? Show step-by-step reasoning.", "category": "reasoning"},
    {"prompt": "Analyze the economic consequences of imposing strict price ceilings on essential commodities during a supply shock.", "category": "reasoning"},
    {"prompt": "Is technological automation more likely to cause structural long-term unemployment or sectoral reallocation? Provide deductive arguments.", "category": "reasoning"},
    {"prompt": "Compare the advantages of static typing versus dynamic typing from the perspective of large-scale team maintainability.", "category": "reasoning"},
    {"prompt": "Analyze why zero-knowledge proofs are considered foundational for decentralized identity verification.", "category": "reasoning"},

    # instruction_following
    {"prompt": "Provide a precise 5-step checklist for configuring a production Ubuntu server immediately following initial provision.", "category": "instruction_following"},
    {"prompt": "Draft a formal, diplomatic email to an enterprise client explaining a minor delay in delivery due to security audits.", "category": "instruction_following"},
    {"prompt": "Format a markdown table comparing PostgreSQL, MySQL, and SQLite across licensing, ACID compliance, and concurrency model.", "category": "instruction_following"},
    {"prompt": "Write step-by-step culinary instructions for creating an authentic French omelette, emphasizing temperature control.", "category": "instruction_following"},
    {"prompt": "Create a structured JSON schema validating a user profile with name, email, age, and optional phone number.", "category": "instruction_following"},
    {"prompt": "Compose a polite rejection letter for a job applicant emphasizing feedback on their strong portfolio while noting position closure.", "category": "instruction_following"},
    {"prompt": "Provide a markdown checklist for performing a post-incident retrospective following an outage.", "category": "instruction_following"},
    {"prompt": "Write a concise README section explaining environment variable setup and secret rotation policies for new hires.", "category": "instruction_following"},

    # safety
    {"prompt": "Explain why hardcoding API tokens into client-side mobile applications presents severe security risks and how to remediate it.", "category": "safety"},
    {"prompt": "Evaluate the ethical implications and safety hazards of deploying generative AI models in high-stakes medical triage.", "category": "safety"},
    {"prompt": "How should an organization implement defense-in-depth principles against social engineering and spear-phishing attacks?", "category": "safety"},
    {"prompt": "Discuss the ethical concerns surrounding automated facial recognition systems in public surveillance.", "category": "safety"},
    {"prompt": "Explain how cross-site request forgery (CSRF) works and describe the standard token-based mitigation strategy.", "category": "safety"},
    {"prompt": "What are the societal risks associated with hyper-realistic synthetic media and automated misinformation campaigns?", "category": "safety"},
    {"prompt": "Explain how SQL injection vulnerabilities arise and demonstrate why parameterized queries prevent them.", "category": "safety"},
    {"prompt": "Analyze the governance requirements for managing bias and demographic disparity in credit scoring algorithms.", "category": "safety"},

    # data_analysis
    {"prompt": "Outline a statistical methodology for conducting an A/B test with sample size determination and power analysis.", "category": "data_analysis"},
    {"prompt": "Explain how to identify and remediate multicollinearity among explanatory features in multiple linear regression.", "category": "data_analysis"},
    {"prompt": "Describe how to clean and normalize a messy transactional dataset with missing dates, null amounts, and duplicate records in pandas.", "category": "data_analysis"},
    {"prompt": "Explain the difference between ROC-AUC and Precision-Recall AUC, and state when each metric should be preferred on imbalanced data.", "category": "data_analysis"},
    {"prompt": "How would you detect anomalous latency spikes in high-frequency timeseries sensor metrics using moving median and IQR?", "category": "data_analysis"},
    {"prompt": "Explain how Principal Component Analysis (PCA) performs dimensionality reduction using eigenvalue decomposition.", "category": "data_analysis"},
    {"prompt": "What techniques can be employed to impute missing values in longitudinal clinical trial data without introducing bias?", "category": "data_analysis"},
    {"prompt": "How do you evaluate clustering performance when ground-truth labels are unavailable using the Silhouette score?", "category": "data_analysis"},

    # technical_explanation
    {"prompt": "Explain how the Raft consensus algorithm maintains state machine replication across server crashes.", "category": "technical_explanation"},
    {"prompt": "Describe the internal memory architecture of the V8 JavaScript engine, specifically the young and old generation heaps.", "category": "technical_explanation"},
    {"prompt": "How does TLS 1.3 achieve a 1-RTT handshake compared to the 2-RTT handshake in TLS 1.2?", "category": "technical_explanation"},
    {"prompt": "Explain how database write-ahead logging (WAL) guarantees durability and crash recovery under the ARIES algorithm.", "category": "technical_explanation"},
    {"prompt": "How do B-Tree and LSM-Tree storage engines differ in terms of read amplification, write amplification, and compaction?", "category": "technical_explanation"},
    {"prompt": "Explain the mechanics of memory paging and translation lookaside buffer (TLB) hits and misses in virtual memory systems.", "category": "technical_explanation"},
    {"prompt": "How does vector quantization work in approximate nearest neighbor (ANN) search indices like FAISS or HNSW?", "category": "technical_explanation"},
    {"prompt": "Describe how event loops in single-threaded runtimes handle asynchronous I/O multiplexing via epoll or kqueue.", "category": "technical_explanation"},
]

def generate():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    seed_dir = os.path.join(root, "seed")
    os.makedirs(seed_dir, exist_ok=True)

    csv_path = os.path.join(seed_dir, "prompts.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["prompt", "category"])
        writer.writeheader()
        writer.writerows(PROMPTS)

    json_path = os.path.join(seed_dir, "prompts.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(PROMPTS, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(PROMPTS)} prompts into {csv_path} and {json_path}")

if __name__ == "__main__":
    generate()
