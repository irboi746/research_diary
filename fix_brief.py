import re

with open("content/news/2026-09-14-daily-brief.md", "r") as f:
    content = f.read()

# Fix the bad splits manually
content = content.replace("- In this work, we present the first large-scale security audit of the arXiv preprint repository, analyzing over 1.\n- 2 TB of data from 100,000 arXiv submissions to report on systemic sensitive information leakage.\n", "- In this work, we present the first large-scale security audit of the arXiv preprint repository, analyzing over 1.2 TB of data from 100,000 arXiv submissions to report on systemic sensitive information leakage.\n")

content = content.replace("- MicroVM-based containers are increasingly deployed in public clouds (e.\n- g.\n- , AWS, Azure, and Alibaba Cloud) to combine container efficiency with strong isolation.\n", "- MicroVM-based containers are increasingly deployed in public clouds (e.g., AWS, Azure, and Alibaba Cloud) to combine container efficiency with strong isolation.\n")

with open("content/news/2026-09-14-daily-brief.md", "w") as f:
    f.write(content)
