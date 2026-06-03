#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           🤖 DENIA BOT v6.0 — ULTIMATE AI AGENT & LEARNING PLATFORM          ║
║    Autonomous Coding · 98 AI Models · Self-Improving · RAG · Education       ║
║                                                                              ║
║  NEW v6.0 FEATURES (30+ upgrades):                                           ║
║  • 98 Real AI Models with exact VND pricing from ckey.vn                     ║
║  • Smart Agent: Model Selection · Cost Warning · Budget Limit · Auto-Retry    ║
║  • Education: 2000 Lessons/Language (1200 Theory 9-Section + 800 LeetCode)    ║
║  • 20+ Programming Languages with full curriculum                             ║
║  • File Format Selector: TXT / JSON / Markdown / Python                     ║
║  • Auto-Conversation Summarization · Persistent JSON State                    ║
║  • Real Web Search (DuckDuckGo) · Matplotlib Sandbox                         ║
║  • Code Formatter (Black/Prettier) · Snippet Manager · Whiteboard             ║
║  • Diff/Patch Viewer · Code Review System · Test Coverage                     ║
║  • GitHub Full CRUD · Voice · Vision · RAG · Scheduled Jobs                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import re
import sys
import tempfile
import time
import traceback
import uuid
import math
import random
import string
import html
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from collections import defaultdict
import textwrap
import subprocess
import shlex

import aiohttp
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand,
    InputFile, InlineQueryResultArticle, InputTextMessageContent
)
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler, InlineQueryHandler
)
from telegram.constants import ParseMode, ChatAction

# ============================ CONFIGURATION ============================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8909561772:AAGQgxrbvXbi-RACF4_Z7iiS4R7NA6Za6wU")
API_KEY = os.getenv("API_KEY", "sk-e317a237354192e26f99951f06e4882779e8a0e08e86d2f71242e8ff770bdf24")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

API_CHAT_URL = "https://ckey.vn/v1/chat/completions"
API_EMBED_URL = "https://ckey.vn/v1/embeddings"
API_TTS_URL = "https://ckey.vn/v1/audio/speech"
API_IMAGE_URL = "https://ckey.vn/v1/images/generations"

STATE_FILE = "/tmp/denia_state_v6.json"
MAX_HISTORY = 64
MAX_OUTPUT_TOKENS = 16384
STATUS_UPDATE_INTERVAL = 2.0
TELEGRAM_MSG_LIMIT = 4096
TELEGRAM_FILE_LIMIT = 20 * 1024 * 1024
AUTO_SUMMARIZE_THRESHOLD = 32
AGENT_MODEL_SELECT, AGENT_CONFIRM = range(2)

# ============================ REAL MODEL PRICING (VND per 1M tokens) ============================

MODEL_PRICING = {
    # FREE / EMBED / TTS
    "vi-VN-HoaiMyNeural": (0, 0), "google-tts/vi": (0, 0), "vi-VN-NamMinhNeural": (0, 0),
    "namtran96hth/MiniMax-M2.7": (0, 0), "thanhnhan9023/gpt-image-2": (0, 0),
    "glm4.7": (1, 1), "mistral-small-4-119b-2603": (1, 1), "text-embedding-3-small": (1, 1),
    "llama-nemotron-embed-vl-1b-v2": (1, 1), "gemini-embedding-2-preview": (1, 1),
    "pplx-embed-v1-4b": (1, 1), "qwen3-coder-480b-a35b-instruct": (1, 1),
    "gemini-embedding-001": (1, 1), "mistral-medium-3.5-128b": (1, 1),
    # LOW COST
    "qwen3-coder-next": (60, 320), "minimax-m2.1": (108, 480), "deepseek-3.2": (112, 168),
    "deepseek-r1-distill-qwen-32b": (120, 120), "minimax-m2.5": (120, 480),
    "mistral-large-3-675b-instruct-2512": (200, 600), "kimi-k2.5": (240, 1000),
    "kimi-k2.6": (296, 1400), "phuocanh421994/Qwen3.7-Plus (Đại hạ giá)": (300, 900),
    "vykelongthuong/Deepseek V4 Flash": (300, 1000), "deepseek-v4-flash": (322, 644),
    "hiennqhust/greg-1-mini": (400, 800), "glm-5": (400, 1280), "gpt-5.4-mini": (400, 2400),
    "wtran6321/gpt-5.4-mini": (480, 2280), "hiennqhust/glm-5.1": (500, 2000),
    "glm-5.1": (500, 2500), "hiennqhust/qwen3.6-27b": (500, 3000),
    "hiennqhust/deepseek-v4-flash": (500, 3000), "claude-haiku-4.5": (600, 3000),
    "vykelongthuong/GPT 5.3 Codex": (600, 4000), "hiennqhust/kimi-k2.6": (666, 2666),
    "phuocanh421994/Deepseek V4 Pro": (700, 1400), "grok-4.20-thinking": (750, 1500),
    "grok-4.3": (750, 1500), "grok-4.20-fast": (750, 1500),
    # MID COST
    "hiennqhust/gpt-5.4": (800, 3000), "w3leee/CodeX GPT 5.4": (900, 8000),
    "3h15pm/CodeX GPT-5.4": (900, 8000), "phuocanh421994/Qwen 3.6 Plus": (1000, 2500),
    "vuduythanh2023/qwen3.7-max": (1000, 3000), "vykelongthuong/Claude Haiku 4.5": (1000, 4000),
    "hiennqhust/deepseek-v4-pro": (1000, 4500), "26479061/claude-haiku-4.5": (1000, 5000),
    "deepseek-v4-pro": (1000, 5000), "nttin213/GPT-5.5": (1000, 6000),
    "gpt-5.4": (1000, 8000), "vykelongthuong/GPT 5.4": (1200, 8000),
    "yudhaekasaputra1/Xiaomi MiMo V2.5": (1250, 1250), "haidinhphu1704/gpt-5.5-codex": (1500, 4000),
    "vuduongcalvin/gemini-3-flash-preview": (1500, 4500), "hiennqhust/mimo-v2.5-pro": (1500, 5000),
    "tranhieu13102003/gpt-5.5[1m]": (1500, 6000), "thanhnhan9023/sl-gpt-5.5": (1500, 7000),
    "vykelongthuong/Claude Sonnet 4.6": (1500, 7000), "phuocanh421994/Qwen 3.7 max": (1500, 7500),
    "wtran6321/gpt-5.5": (1580, 7880), "hiennqhust/gpt-5.5": (1700, 8500),
    "3h15pm/CodeX GPT-5.5": (1700, 11100),
    # HIGH COST
    "claude-sonnet-4": (1800, 9000), "claude-sonnet-4.5": (1800, 9000),
    "claude-sonnet-4-5": (1800, 9000), "claude-sonnet-4.6[1m]": (1800, 9000),
    "claude-sonnet-4.6": (1800, 9000), "claude-sonnet-4-6": (1800, 9000),
    "claude-sonnet-4-6[1m]": (1800, 9000), "vykelongthuong/GPT 5.5": (1800, 9000),
    "w3leee/CodeX GPT 5.5": (1800, 10000), "wtran6321/gpt-5.5-xhigh": (1880, 9880),
    "namnv/Claude Opus 4.6 + GPT 5.5": (2000, 5000), "toanthinhx64/claude-opus-4-6": (2000, 6000),
    "toanthinhx64/claude-opus-4-7": (2000, 8000), "26479061/claude-sonnet-4-6": (2000, 10000),
    "26479061/gpt-5.5": (2000, 10000), "toanthinhx64/gpt-5.5": (2000, 10000),
    "gpt-5.5": (2000, 12000), "pqminh4/My gpt-5.5": (2000, 12000),
    "tranhieu13102003/claude-opus-4.7 kiro[1m]": (2000, 10000000),
    "yudhaekasaputra1/Xiaomi MiMo V2.5 Pro": (2500, 2500),
    "haidinhphu1704/claude-opus-4.8-kiro": (2600, 5444),
    "vuduongcalvin/gemini-3.5-flash": (3000, 12000),
    "claude-opus-4-6": (3000, 15000), "claude-opus-4-6[1m]": (3000, 15000),
    "claude-opus-4.6": (3000, 15000), "claude-opus-4.6[1m]": (3000, 15000),
    "26479061/claude-opus-4-6": (3500, 17500), "vykelongthuong/Claude Opus 4.6": (4000, 12000),
    "claude-opus-4.8": (4000, 20000), "claude-opus-4.7": (4000, 20000),
    "claude-opus-4-7[1m]": (4000, 20000), "claude-opus-4.7[1m]": (4000, 20000),
    "26479061/claude-opus-4.8": (4200, 23000), "toanthinhx64/claude-opus-4.7": (5000, 25000),
    "thanhnhan9023/gemini-3.1-pro": (9000, 35000),
}

CATEGORY_EMOJI = {
    "GPT": "🟢", "Claude": "🟣", "Gemini": "🔵", "GLM": "🟡",
    "Qwen": "🟠", "MiniMax": "🔴", "Mistral": "⚪", "DeepSeek": "⚫",
    "Open-source": "🟤", "Grok": "🟩", "Kimi": "🟦", "Khac": "⬜",
    "Free": "💚", "Low": "💚", "Mid": "💛", "High": "🧡", "Ultra": "❤️", "Special": "💜"
}

SYSTEM_PROMPT = """You are Denia Bot v6.0 — an autonomous, self-improving AI agent with advanced reasoning and teaching capabilities.

CORE CAPABILITIES:
1. Write, analyze, debug, refactor, and optimize code in ANY language
2. Full GitHub integration: repos, files, branches, PRs, issues, releases, actions
3. Advanced code analysis: syntax, logic, security, performance, style, complexity
4. Self-training: auto-fix errors, learn from failures, improve over time
5. Multi-step reasoning: plan, execute, verify, report
6. RAG knowledge base: ingest documents, answer accurately
7. Web search: real-time information retrieval and synthesis
8. Data analysis: Python execution, chart generation, statistical analysis
9. EDUCATION: Teach programming with structured 9-section lessons and LeetCode problems

AGENT BEHAVIOR:
- Always provide COMPLETE, runnable, production-ready code
- Include error handling, logging, type hints, docstrings
- Design for scalability, security, and maintainability
- Explain reasoning step-by-step; offer alternatives
- If uncertain, admit it honestly rather than hallucinate
- Use Vietnamese for casual chat, English for technical/code tasks unless requested otherwise
- For EDUCATION mode: strictly follow the 9-section lesson format

SELF-IMPROVEMENT PROTOCOL:
- After each task: reflect, identify improvements, update knowledge
- Maintain user preference profiles (coding style, verbosity, language)
- Track success/failure patterns and adapt strategies
- Proactively suggest optimizations and best practices
"""

AGENT_SYSTEM_PROMPT = """You are Denia Bot in AGENT MODE — an autonomous software engineering agent.

MISSION: Complete coding tasks end-to-end with zero human intervention.

WORKFLOW (MANDATORY):
1. ANALYZE: Fully understand requirements, constraints, edge cases
2. PLAN: Create detailed implementation plan with file structure
3. ARCHITECT: Design scalable, secure, maintainable system
4. CODE: Write complete, documented, tested code for ALL files
5. REVIEW: Self-review for bugs, security issues, performance
6. TEST: Generate unit tests, integration tests, verify syntax
7. DOCUMENT: Write README, API docs, deployment guide
8. PUSH: Create GitHub repo, commit all files with proper messages
9. VERIFY: Confirm repo is accessible and files are correct
10. REPORT: Summarize with links, metrics, and next steps

CODE QUALITY STANDARDS:
- PEP 8 / Google Style / Standard conventions
- Comprehensive error handling and logging
- Input validation and sanitization
- No hardcoded secrets (use env vars)
- Async where appropriate, thread-safe
- Include __main__ guards and example usage

GITHUB OPERATIONS:
- Create repo with README, .gitignore, LICENSE
- Use conventional commits (feat:, fix:, docs:, test:)
- Protect main branch, use feature branches for PRs
- Set up GitHub Actions CI/CD when applicable
- Create releases with semantic versioning

SECURITY CHECKLIST:
- No SQL injection, XSS, command injection vulnerabilities
- Proper auth/authorization patterns
- Secure secret management
- Input validation on all boundaries
- Dependency vulnerability scanning
"""

LESSON_SYSTEM_PROMPT = """You are Denia Bot in TEACHER MODE — an expert programming instructor.

When generating a theory lesson, you MUST follow this exact 9-section structure:

===SECTION 1: NHẮC LẠI BÀI CŨ===
Briefly summarize key concepts from previous lessons (2-3 bullet points).

===SECTION 2: NỘI DUNG BÀI MỚI===
Introduce the new topic clearly. Explain what the user will learn and why it matters.

===SECTION 3: CẤU TRÚC BÀI MỚI===
Outline the structure: main concepts, sub-topics, flow of learning.

===SECTION 4: GIẢI THÍCH THUẬT NGỮ===
Define all technical terms introduced in this lesson with simple explanations and Vietnamese translations where helpful.

===SECTION 5: CODE CHỦ ĐẠO===
Provide the main, complete, runnable code example. Must be production-quality with comments.

===SECTION 6: GIẢI THÍCH CODE===
Line-by-line or block-by-block explanation of the code above.

===SECTION 7: CHỐT LẠI===
Summarize 3-5 key takeaways from this lesson.

===SECTION 8: 3 CÂU HỎI===
Ask 3 thought-provoking questions to test understanding. Include answers hidden in <!-- --> HTML comments.

===SECTION 9: LEETCODE MINI===
Provide a small coding challenge (easier than full LeetCode) related to this lesson. Include:
- Problem statement
- Input/Output examples
- Starter code
- Solution (hidden in comments)

RULES:
- Use Vietnamese for explanations, English for code and technical terms
- Code must be complete and runnable
- Progress gradually from basic to advanced
- Connect theory to real-world applications
"""

DEFAULT_MODE = "chat"
DEFAULT_CHAT_MODEL = "deepseek-v4-pro"
DEFAULT_AGENT_MODEL = "claude-opus-4.6"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_TTS_MODEL = "google-tts/vi"
DEFAULT_VISION_MODEL = "gpt-5.4"
DEFAULT_LESSON_MODEL = "claude-sonnet-4.6"

# ============================ LEARNING CURRICULUM ============================

LEARNING_LANGUAGES = [
    "python", "javascript", "java", "cpp", "go", "rust", "typescript",
    "ruby", "php", "swift", "kotlin", "csharp", "sql", "bash",
    "r", "matlab", "scala", "dart", "lua", "perl", "julia",
    "haskell", "elixir", "erlang", "clojure", "ocaml"
]

LANGUAGE_DISPLAY = {
    "python": "Python 🐍", "javascript": "JavaScript 🟨", "java": "Java ☕",
    "cpp": "C++ 🔵", "go": "Go 🐹", "rust": "Rust 🦀", "typescript": "TypeScript 📘",
    "ruby": "Ruby 💎", "php": "PHP 🐘", "swift": "Swift 🍎", "kotlin": "Kotlin 📱",
    "csharp": "C# 🎮", "sql": "SQL 🗄️", "bash": "Bash 🐚", "r": "R 📊",
    "matlab": "MATLAB 🔢", "scala": "Scala ⚡", "dart": "Dart 🎯", "lua": "Lua 🌙",
    "perl": "Perl 🐪", "julia": "Julia 🔴", "haskell": "Haskell 🟣",
    "elixir": "Elixir 💧", "erlang": "Erlang 📡", "clojure": "Clojure 🔷",
    "ocaml": "OCaml 🐫"
}

# Theory topics per language (60 topics = ~20 lessons each = 1200 lessons)
THEORY_TOPICS = {
    "python": [
        "Fundamentals", "Variables & Types", "Operators", "Control Flow", "Loops",
        "Functions", "Lambda & Map/Filter", "Modules & Packages", "File I/O",
        "Error Handling", "OOP Basics", "Classes & Objects", "Inheritance",
        "Polymorphism", "Encapsulation", "Dunder Methods", "Iterators & Generators",
        "Decorators", "Context Managers", "Collections Module", "List/Dict Comprehensions",
        "Regular Expressions", "Datetime & Time", "JSON & XML", "Database Basics",
        "SQLite", "SQLAlchemy ORM", "Web Basics", "HTTP & APIs", "Requests Library",
        "Flask Framework", "FastAPI Framework", "Django Basics", "Django ORM",
        "Django REST", "Asyncio Basics", "Async/Await", "Aiohttp", "Threading",
        "Multiprocessing", "Concurrent Futures", "NumPy Basics", "Pandas Basics",
        "Data Visualization", "Matplotlib", "Seaborn", "Machine Learning Intro",
        "Scikit-learn", "Testing & Pytest", "Mocking", "TDD", "Design Patterns",
        "SOLID Principles", "Clean Code", "Performance Optimization", "Memory Management",
        "Cython & Extensions", "Packaging & Distribution", "Docker & Deployment",
        "CI/CD Basics", "Git Advanced", "Security Best Practices", "Web Scraping",
        "Selenium & Automation", "Advanced Python"
    ],
    "javascript": [
        "Fundamentals", "Variables & Scope", "Data Types", "Operators", "Control Flow",
        "Functions", "Arrow Functions", "Closures", "Hoisting", "Objects & Prototypes",
        "ES6+ Features", "Classes", "Inheritance", "Modules", "Promises",
        "Async/Await", "Event Loop", "Callbacks", "Error Handling", "DOM Manipulation",
        "Events", "Forms & Validation", "Local Storage", "Fetch API", "AJAX",
        "Node.js Basics", "Express.js", "Middleware", "Routing", "REST API",
        "MongoDB & Mongoose", "Authentication", "JWT & OAuth", "WebSockets",
        "Socket.io", "React Basics", "JSX", "Components", "Props & State",
        "Hooks", "useEffect", "Context API", "Redux", "React Router",
        "Next.js", "Vue.js Basics", "Angular Basics", "TypeScript Integration",
        "Jest Testing", "E2E Testing", "Webpack & Bundlers", "Babel",
        "Performance", "Memory Leaks", "Security XSS/CSRF", "Progressive Web Apps",
        "Service Workers", "WebAssembly", "Micro-frontends", "Design Patterns JS",
        "Functional Programming", "Advanced JS"
    ],
    "java": [
        "Fundamentals", "JVM & JDK", "Variables & Types", "Operators", "Control Flow",
        "Arrays", "Methods", "OOP Basics", "Classes & Objects", "Constructors",
        "Inheritance", "Polymorphism", "Abstraction", "Interfaces", "Encapsulation",
        "Packages", "Access Modifiers", "Static & Final", "Inner Classes", "Enums",
        "Generics", "Collections Framework", "List & Set", "Map & Queue",
        "ArrayList vs LinkedList", "HashMap Internals", "Comparable & Comparator",
        "Iterators", "Streams API", "Lambda Expressions", "Method References",
        "Optional", "Date & Time API", "IO Streams", "NIO.2", "Serialization",
        "Multithreading", "Synchronization", "Executors", "Concurrent Collections",
        "Locks", "Atomic Variables", "Thread Pools", "Fork/Join", "JDBC",
        "Hibernate ORM", "JPA", "Spring Basics", "Spring Boot", "DI & IoC",
        "Spring MVC", "Spring REST", "Spring Security", "Spring Data JPA",
        "Spring Testing", "Maven & Gradle", "JUnit & Mockito", "Logging",
        "Design Patterns", "SOLID", "Clean Architecture", "Microservices",
        "Docker & Kubernetes", "CI/CD", "Performance Tuning", "JVM Internals",
        "Garbage Collection", "Java 17+ Features", "Advanced Java"
    ],
    "cpp": [
        "Fundamentals", "Compilation Process", "Variables & Types", "Operators",
        "Control Flow", "Arrays & Strings", "Pointers", "References", "Functions",
        "Function Overloading", "Default Arguments", "Inline Functions", "OOP Basics",
        "Classes & Objects", "Constructors & Destructors", "Copy Constructor",
        "Assignment Operator", "Move Semantics", "Inheritance", "Virtual Functions",
        "Polymorphism", "Abstract Classes", "Operator Overloading", "Templates",
        "STL Containers", "Vector & List", "Map & Set", "Iterators", "Algorithms",
        "Functors", "Lambdas", "Smart Pointers", "Memory Management", "RAII",
        "Exception Handling", "File I/O", "Streams", "Multithreading", "Mutex & Locks",
        "Condition Variables", "Atomic Operations", "Thread Local", "Async & Futures",
        "Networking", "Sockets", "CMake & Build Systems", "Makefiles", "Debugging",
        "Profiling", "Valgrind", "Design Patterns", "Singleton", "Factory", "Observer",
        "Strategy", "Modern C++11/14/17/20", "Auto & Decltype", "Range-based For",
        "Constexpr", "Concepts C++20", "Modules C++20", "Coroutines", "Advanced C++"
    ],
    "go": [
        "Fundamentals", "Setup & Workspace", "Variables & Types", "Operators",
        "Control Flow", "Arrays & Slices", "Maps", "Structs", "Functions",
        "Multiple Returns", "Named Returns", "Variadic Functions", "Closures",
        "Methods", "Pointers", "Interfaces", "Embedding", "Type Assertions",
        "Goroutines", "Channels", "Buffered Channels", "Select Statement",
        "Sync Package", "Mutex", "RWMutex", "WaitGroups", "Once & Pool",
        "Context Package", "Error Handling", "Panic & Recover", "Defer",
        "Testing", "Benchmarking", "Table Driven Tests", "Mocking", "JSON",
        "HTTP Server", "HTTP Client", "Middleware", "Routing", "Templates",
        "Databases", "SQLx", "GORM", "Redis", "Caching", "Logging",
        "Zap & Logrus", "Configuration", "Environment Variables", "CLI Apps",
        "Cobra & Viper", "Concurrency Patterns", "Worker Pools", "Pipelines",
        "Fan-out Fan-in", "Context Cancellation", "Graceful Shutdown", "Docker",
        "Microservices", "gRPC", "Protocol Buffers", "Testing Integration",
        "Profiling", "pprof", "Deployment", "CI/CD", "Advanced Go"
    ],
    "rust": [
        "Fundamentals", "Ownership", "Borrowing", "Lifetimes", "Variables & Types",
        "Control Flow", "Functions", "Structs", "Enums", "Pattern Matching",
        "Methods", "Generics", "Traits", "Trait Bounds", "Associated Types",
        "Drop Trait", "Copy & Clone", "Smart Pointers", "Box", "Rc & Arc",
        "RefCell", "Mutex & RwLock", "Collections", "Vector", "HashMap",
        "Strings", "Slices", "Iterators", "Closures", "Modules", "Crates",
        "Cargo & Dependencies", "Error Handling", "Result & Option", "? Operator",
        "Custom Errors", "Testing", "Unit Tests", "Integration Tests", "Documentation",
        "Macros", "Declarative Macros", "Procedural Macros", "Unsafe Rust",
        "FFI", "Lifetimes Advanced", "Higher-Ranked Traits", "Async Rust",
        "Futures", "Tokio Runtime", "Async/Await", "Streams", "Channels",
        "Select", "Pin & Unpin", "Networking", "Web Frameworks", "Actix",
        "Axum", "Rocket", "Database", "Diesel", "SQLx", "WebAssembly",
        "Concurrency", "Parallelism", "Rayon", "Performance", "Benchmarking",
        "Clippy & Fmt", "CI/CD", "Deployment", "Advanced Rust"
    ],
    "typescript": [
        "Fundamentals", "Types vs Interfaces", "Basic Types", "Arrays & Tuples",
        "Enums", "Any & Unknown", "Type Inference", "Type Assertions", "Functions",
        "Optional Parameters", "Default Parameters", "Rest Parameters", "Overloads",
        "Generics", "Generic Constraints", "Generic Classes", "Utility Types",
        "Partial & Required", "Readonly & Record", "Pick & Omit", "ReturnType",
        "Classes", "Access Modifiers", "Abstract Classes", "Inheritance", "Interfaces",
        "Extending Interfaces", "Declaration Merging", "Modules", "Namespaces",
        "Module Resolution", "Decorators", "Metadata", "tsconfig.json", "Compiler Options",
        "Strict Mode", "Type Guards", "Custom Type Guards", "Discriminated Unions",
        "Mapped Types", "Conditional Types", "Template Literal Types", "Infer Keyword",
        "Type Challenges", "Advanced Patterns", "React & TS", "Hooks & TS",
        "Context & TS", "Redux & TS", "Node.js & TS", "Express & TS", "Testing",
        "Jest & TS", "Mocking Types", "API Clients", "GraphQL & TS", "Prisma ORM",
        "Monorepos", "Turborepo", "Nx", "Performance", "Bundle Analysis",
        "Linting", "ESLint & Prettier", "CI/CD", "Deployment", "Advanced TypeScript"
    ],
    "sql": [
        "Fundamentals", "Relational Databases", "SQL Syntax", "SELECT Basics",
        "WHERE Clause", "AND OR NOT", "ORDER BY", "LIMIT & OFFSET", "Aggregate Functions",
        "COUNT SUM AVG", "GROUP BY", "HAVING", "JOIN Basics", "INNER JOIN",
        "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "CROSS JOIN", "SELF JOIN",
        "UNION", "Subqueries", "Correlated Subqueries", "EXISTS & IN",
        "INSERT", "UPDATE", "DELETE", "TRUNCATE", "CREATE TABLE",
        "Data Types", "Constraints", "Primary Key", "Foreign Key", "Unique",
        "Check & Default", "Indexes", "B-Tree Indexes", "Composite Indexes",
        "Query Optimization", "EXPLAIN PLAN", "Views", "Stored Procedures",
        "Functions", "Triggers", "Transactions", "ACID", "Isolation Levels",
        "Locking", "Deadlocks", "Normalization", "1NF 2NF 3NF", "Denormalization",
        "Database Design", "ER Diagrams", "Advanced SELECT", "Window Functions",
        "ROW_NUMBER", "RANK & DENSE_RANK", "LEAD & LAG", "NTILE", "CTEs",
        "Recursive CTEs", "PIVOT & UNPIVOT", "Temporal Queries", "Full-Text Search",
        "NoSQL Comparison", "MongoDB Basics", "Redis Basics", "PostgreSQL Advanced",
        "MySQL Advanced", "Backup & Restore", "Replication", "Sharding",
        "Partitioning", "Security", "Injection Prevention", "Advanced SQL"
    ],
}

# Default topics for languages without specific curriculum
DEFAULT_TOPICS = [
    "Fundamentals", "Variables & Types", "Operators", "Control Flow", "Loops",
    "Functions", "Arrays & Collections", "Strings", "OOP Basics", "Classes",
    "Inheritance", "Polymorphism", "Error Handling", "File I/O", "Modules",
    "Standard Library", "Third-party Libraries", "Testing", "Debugging",
    "Performance", "Memory Management", "Concurrency", "Networking", "Web Development",
    "Database", "Security", "Best Practices", "Design Patterns", "Refactoring",
    "Deployment", "CI/CD", "Advanced Topics"
]

# 800 LeetCode problems organized by topic and difficulty
LEETCODE_TOPICS = [
    "Array & String", "Two Pointers", "Sliding Window", "Stack & Queue",
    "Linked List", "Binary Tree", "BST", "Heap & Priority Queue", "Backtracking",
    "Trie", "Graph", "DFS & BFS", "Union Find", "Topological Sort",
    "Dynamic Programming", "Greedy", "Bit Manipulation", "Math", "Recursion",
    "Design", "SQL", "Multi-threading", "Advanced Algorithms"
]

LEETCODE_DIFFICULTIES = ["Easy", "Medium", "Hard"]

# Generate 800 problem slots
LEETCODE_BANK = {}
problem_id = 1
for topic in LEETCODE_TOPICS:
    LEETCODE_BANK[topic] = []
    for diff in LEETCODE_DIFFICULTIES:
        count = 12 if diff == "Easy" else 15 if diff == "Medium" else 8
        for i in range(count):
            LEETCODE_BANK[topic].append({
                "id": problem_id,
                "topic": topic,
                "difficulty": diff,
                "title": f"{topic} Problem {i+1} ({diff})",
                "generated": False
            })
            problem_id += 1

# ============================ LOGGING ============================

logging.basicConfig(
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/tmp/denia_bot_v6.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================ DATA MODELS ============================

@dataclass
class UserStats:
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_vnd: float = 0.0
    total_latency: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    files_processed: int = 0
    code_executed: int = 0
    lessons_completed: int = 0
    leetcode_solved: int = 0
    first_seen: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_active: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class AgentTask:
    task_id: str
    description: str
    selected_model: str = ""
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    files_created: List[str] = field(default_factory=list)
    repo_url: Optional[str] = None
    plan: Optional[str] = None
    code_review: Optional[str] = None
    test_results: Optional[str] = None
    cost_vnd: float = 0.0

@dataclass
class KnowledgeDocument:
    doc_id: str
    filename: str
    content: str
    embedding: Optional[List[float]] = None
    uploaded_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    chunk_count: int = 0

@dataclass
class ScheduledJob:
    job_id: str
    user_id: int
    description: str
    trigger_time: datetime
    command: str
    args: str
    is_recurring: bool = False
    cron_expr: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class ConversationBranch:
    branch_id: str
    parent_id: Optional[str]
    name: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class UserPreferences:
    language: str = "auto"
    code_style: str = "pep8"
    verbosity: str = "balanced"
    theme: str = "default"
    auto_execute: bool = False
    default_mode: str = "chat"
    preferred_models: Dict[str, str] = field(default_factory=dict)
    notifications: bool = True
    file_format: str = "txt"
    budget_limit_vnd: float = 0.0
    learning_language: str = "python"
    learning_level: str = "beginner"

@dataclass
class LessonProgress:
    language: str
    current_lesson: int = 0
    completed_lessons: List[int] = field(default_factory=list)
    quiz_scores: Dict[int, int] = field(default_factory=dict)
    leetcode_solved: List[int] = field(default_factory=list)
    last_studied: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class ConversationState:
    history: List[Dict[str, str]] = field(default_factory=list)
    mode: str = DEFAULT_MODE
    current_model: str = DEFAULT_CHAT_MODEL
    stats: UserStats = field(default_factory=UserStats)
    agent_tasks: List[AgentTask] = field(default_factory=list)
    github_username: Optional[str] = None
    preferred_style: str = "clean"
    last_error: Optional[str] = None
    self_notes: List[str] = field(default_factory=list)
    knowledge_base: List[KnowledgeDocument] = field(default_factory=list)
    branches: Dict[str, ConversationBranch] = field(default_factory=dict)
    current_branch_id: str = "main"
    preferences: UserPreferences = field(default_factory=UserPreferences)
    scheduled_jobs: List[ScheduledJob] = field(default_factory=list)
    temp_files: List[str] = field(default_factory=list)
    context_summary: Optional[str] = None
    lesson_progress: Dict[str, LessonProgress] = field(default_factory=dict)
    pending_agent_task: Optional[str] = None
    pending_agent_model: Optional[str] = None
    whiteboard: str = ""
    snippet_storage: Dict[str, str] = field(default_factory=dict)
    last_model_warning: str = ""

# ============================ STATE MANAGEMENT ============================

user_states: Dict[int, ConversationState] = {}
scheduled_jobs_global: List[ScheduledJob] = []

def _load_state():
    global user_states
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for uid_str, sdata in data.items():
                uid = int(uid_str)
                state = ConversationState()
                state.mode = sdata.get("mode", DEFAULT_MODE)
                state.current_model = sdata.get("current_model", DEFAULT_CHAT_MODEL)
                state.github_username = sdata.get("github_username")
                state.self_notes = sdata.get("self_notes", [])
                state.current_branch_id = sdata.get("current_branch_id", "main")
                state.whiteboard = sdata.get("whiteboard", "")
                state.last_model_warning = sdata.get("last_model_warning", "")
                if "preferences" in sdata:
                    p = sdata["preferences"]
                    state.preferences = UserPreferences(**p)
                if "stats" in sdata:
                    state.stats = UserStats(**sdata["stats"])
                if "lesson_progress" in sdata:
                    for lang, lp in sdata["lesson_progress"].items():
                        state.lesson_progress[lang] = LessonProgress(**lp)
                if "branches" in sdata:
                    for bid, bdata in sdata["branches"].items():
                        branch = ConversationBranch(bid, None, bdata.get("name", "Branch"))
                        branch.messages = bdata.get("messages", [])
                        state.branches[bid] = branch
                if "snippet_storage" in sdata:
                    state.snippet_storage = sdata["snippet_storage"]
                user_states[uid] = state
    except Exception as e:
        logger.error(f"State load error: {e}")

def _save_state():
    try:
        data = {}
        for uid, state in user_states.items():
            data[str(uid)] = {
                "mode": state.mode,
                "current_model": state.current_model,
                "stats": asdict(state.stats),
                "github_username": state.github_username,
                "preferences": asdict(state.preferences),
                "self_notes": state.self_notes,
                "lesson_progress": {k: asdict(v) for k, v in state.lesson_progress.items()},
                "branches": {k: {"name": v.name, "messages": v.messages} for k, v in state.branches.items()},
                "current_branch_id": state.current_branch_id,
                "whiteboard": state.whiteboard,
                "last_model_warning": state.last_model_warning,
                "snippet_storage": state.snippet_storage,
            }
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"State save error: {e}")

async def get_user_state(user_id: int) -> ConversationState:
    if user_id not in user_states:
        user_states[user_id] = ConversationState()
        main_branch = ConversationBranch("main", None, "Main Conversation")
        user_states[user_id].branches["main"] = main_branch
        user_states[user_id].lesson_progress["python"] = LessonProgress("python")
        _save_state()
    return user_states[user_id]

def generate_task_id() -> str:
    return f"task_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"

def generate_doc_id() -> str:
    return f"doc_{uuid.uuid4().hex[:8]}"

def generate_branch_id() -> str:
    return f"branch_{uuid.uuid4().hex[:6]}"

def generate_job_id() -> str:
    return f"job_{uuid.uuid4().hex[:8]}"

def generate_snippet_id() -> str:
    return f"snp_{uuid.uuid4().hex[:6]}"

def get_mode_models(mode: str):
    return MODE_CONFIG[mode]["models"]

def get_default_model(mode: str):
    return MODE_CONFIG[mode]["default"]

def get_model_display(mode: str, model_id: str) -> str:
    for cat, mid, disp, tier, inp, out in MODE_CONFIG[mode]["models"]:
        if mid == model_id:
            return f"{CATEGORY_EMOJI.get(tier, '⚪')} {CATEGORY_EMOJI.get(cat, '⚪')} {disp.split(' (')[0]}"
    return model_id

def get_model_category(mode: str, model_id: str) -> str:
    for cat, mid, disp, tier, inp, out in MODE_CONFIG[mode]["models"]:
        if mid == model_id:
            return cat
    return "Khac"

def get_model_tier(mode: str, model_id: str) -> str:
    for cat, mid, disp, tier, inp, out in MODE_CONFIG[mode]["models"]:
        if mid == model_id:
            return tier
    return "Unknown"

def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    if model_id not in MODEL_PRICING:
        return 0.0
    inp_price, out_price = MODEL_PRICING[model_id]
    return (input_tokens * inp_price / 1_000_000) + (output_tokens * out_price / 1_000_000)

def get_model_cost_warning(model_id: str) -> str:
    if model_id not in MODEL_PRICING:
        return "⚠️ Khong co thong tin gia"
    inp, out = MODEL_PRICING[model_id]
    if inp == 0 and out == 0:
        return f"💚 Model *{model_id}* — MIEN PHI (Free)"
    tier = "Free" if inp <= 1 else "Low" if inp <= 500 else "Mid" if inp <= 1500 else "High" if inp <= 3000 else "Ultra" if inp <= 5000 else "Special"
    emoji = CATEGORY_EMOJI.get(tier, "⚪")
    return f"{emoji} Model *{model_id}* — Nhom *{tier}* — Gia: `{inp}`/`{out}` VND/1M tok"

def check_budget_warning(state: ConversationState, estimated_cost: float = 0) -> Optional[str]:
    limit = state.preferences.budget_limit_vnd
    if limit > 0 and (state.stats.total_cost_vnd + estimated_cost) > limit:
        return f"⚠️ CANH BAO: Chi phi hien tai `{state.stats.total_cost_vnd:.0f}` VND da vuot qua gioi han `{limit:.0f}` VND!"
    if limit > 0:
        remaining = limit - state.stats.total_cost_vnd
        if remaining < limit * 0.2:
            return f"⚠️ Chi phi con lai: `{remaining:.0f}` VND ({remaining/limit*100:.0f}%)"
    return None

# ============================ MODEL CATALOG ============================

def _make_models():
    free, low, mid, high, ultra, special = [], [], [], [], [], []
    for model_id, (inp, out) in MODEL_PRICING.items():
        if inp == 0 and out == 0:
            tier = "Free"
        elif inp <= 1:
            tier = "Free"
        elif inp <= 500:
            tier = "Low"
        elif inp <= 1500:
            tier = "Mid"
        elif inp <= 3000:
            tier = "High"
        elif inp <= 5000:
            tier = "Ultra"
        else:
            tier = "Special"
        price_str = f"{inp}/{out}"
        display = f"{model_id.split('/')[-1][:24]} ({price_str}d)"
        cat = "Khac"
        if "gpt" in model_id.lower(): cat = "GPT"
        elif "claude" in model_id.lower(): cat = "Claude"
        elif "deepseek" in model_id.lower(): cat = "DeepSeek"
        elif "qwen" in model_id.lower(): cat = "Qwen"
        elif "glm" in model_id.lower(): cat = "GLM"
        elif "mistral" in model_id.lower(): cat = "Mistral"
        elif "minimax" in model_id.lower() or "m2" in model_id.lower(): cat = "MiniMax"
        elif "grok" in model_id.lower(): cat = "Grok"
        elif "kimi" in model_id.lower(): cat = "Kimi"
        elif "gemini" in model_id.lower(): cat = "Gemini"
        elif "llama" in model_id.lower(): cat = "Open-source"
        elif "mimo" in model_id.lower(): cat = "Open-source"
        elif "embed" in model_id.lower(): cat = "Embed"
        elif "tts" in model_id.lower() or "neural" in model_id.lower(): cat = "TTS"
        entry = (cat, model_id, display, tier, inp, out)
        if tier == "Free": free.append(entry)
        elif tier == "Low": low.append(entry)
        elif tier == "Mid": mid.append(entry)
        elif tier == "High": high.append(entry)
        elif tier == "Ultra": ultra.append(entry)
        else: special.append(entry)
    return free + low + mid + high + ultra + special

ALL_CHAT_MODELS = _make_models()
CHAT_MODELS = [m for m in ALL_CHAT_MODELS if m[1] not in ("text-embedding-3-small", "gemini-embedding-001", "gemini-embedding-2-preview", "pplx-embed-v1-4b", "llama-nemotron-embed-vl-1b-v2", "google-tts/vi", "vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural", "thanhnhan9023/gpt-image-2")]
EMBED_MODELS = [
    ("Embed", "text-embedding-3-small", "Text Embed 3 Small (1/1)", "Free", 1, 1),
    ("Embed", "gemini-embedding-001", "Gemini Embed 001 (1/1)", "Free", 1, 1),
    ("Embed", "gemini-embedding-2-preview", "Gemini Embed 2 Preview (1/1)", "Free", 1, 1),
    ("Embed", "pplx-embed-v1-4b", "PPLX Embed v1 (1/1)", "Free", 1, 1),
    ("Embed", "llama-nemotron-embed-vl-1b-v2", "Llama Nemotron Embed (1/1)", "Free", 1, 1),
]
TTS_MODELS = [
    ("TTS", "google-tts/vi", "Google TTS Vi (0/0)", "Free", 0, 0),
    ("TTS", "vi-VN-HoaiMyNeural", "HoaiMy Neural (0/0)", "Free", 0, 0),
    ("TTS", "vi-VN-NamMinhNeural", "NamMinh Neural (0/0)", "Free", 0, 0),
]
IMAGE_MODELS = [
    ("Image", "thanhnhan9023/gpt-image-2", "GPT Image 2 (0/0+1600/img)", "Free", 0, 0),
]

MODE_CONFIG = {
    "chat": {"name": "💬 Chat", "models": CHAT_MODELS, "default": DEFAULT_CHAT_MODEL, "endpoint": API_CHAT_URL},
    "agent": {"name": "🤖 Agent", "models": CHAT_MODELS, "default": DEFAULT_AGENT_MODEL, "endpoint": API_CHAT_URL},
    "coder": {"name": "💻 Coder", "models": [(c, m, d, t, i, o) for c, m, d, t, i, o in CHAT_MODELS if "codex" in m.lower() or "coder" in m.lower() or "opus" in m.lower() or "deepseek" in m.lower()], "default": "claude-opus-4.6", "endpoint": API_CHAT_URL},
    "embed": {"name": "📊 Embed", "models": EMBED_MODELS, "default": DEFAULT_EMBED_MODEL, "endpoint": API_EMBED_URL},
    "tts": {"name": "🔊 TTS", "models": TTS_MODELS, "default": DEFAULT_TTS_MODEL, "endpoint": API_TTS_URL},
    "vision": {"name": "👁 Vision", "models": [(c, m, d, t, i, o) for c, m, d, t, i, o in CHAT_MODELS if "gpt" in m or "claude" in m or "gemini" in m][:15], "default": DEFAULT_VISION_MODEL, "endpoint": API_CHAT_URL},
    "lesson": {"name": "📚 Lesson", "models": CHAT_MODELS, "default": DEFAULT_LESSON_MODEL, "endpoint": API_CHAT_URL},
}

# ============================ UTILITIES ============================

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text.encode('utf-8')) // 4)

def truncate_text(text: str, max_len: int = 4000) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)[:50]

def sanitize_repo_name(name: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9_-]', '-', name.lower().strip())
    name = re.sub(r'-+', '-', name).strip('-')
    return name or "denia-project"

def format_vnd(amount: float) -> str:
    if amount >= 1000:
        return f"{amount/1000:.1f}k"
    return f"{amount:.0f}"

def build_progress_bar(step: int, total: int, width: int = 20) -> str:
    filled = int(width * step / total)
    return "█" * filled + "░" * (width - filled)

def escape_markdown(text: str) -> str:
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for ch in chars:
        text = text.replace(ch, f'\\{ch}')
    return text

def split_long_text(text: str, max_len: int = 4000) -> List[str]:
    if len(text) <= max_len:
        return [text]
    parts = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        split_at = text.rfind('\n', 0, max_len)
        if split_at == -1:
            split_at = max_len
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    return parts

async def send_long_text(update: Update, text: str, filename: str = "response.txt", caption: str = None, format_hint: str = None):
    if not text:
        return
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    fmt = format_hint or state.preferences.file_format

    if len(text) <= TELEGRAM_MSG_LIMIT:
        for part in split_long_text(text, TELEGRAM_MSG_LIMIT):
            try:
                await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                try:
                    await update.message.reply_text(part, parse_mode=ParseMode.HTML)
                except Exception:
                    await update.message.reply_text(part)
        return

    # File format selection
    ext = fmt if fmt in ("txt", "json", "md", "py") else "txt"
    if fmt == "json":
        try:
            content = json.dumps({"response": text, "timestamp": datetime.now().isoformat()}, ensure_ascii=False, indent=2)
        except:
            content = text
    elif fmt == "md":
        content = f"# Denia Bot Response\n\n*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n---\n\n{text}"
    elif fmt == "py":
        content = f'"""\nDenia Bot Response\nGenerated: {datetime.now().isoformat()}\n"""\n\nresponse = """\n{text}\n"""'
    else:
        content = text

    bio = io.BytesIO(content.encode('utf-8'))
    bio.name = filename.replace('.txt', f'.{ext}')
    cap = caption or f"Phan hoi qua dai ({len(text)} ky tu), da gui duoi dang file .{ext}"
    await update.message.reply_document(document=bio, caption=cap)

def build_metrics_footer(metrics: Dict[str, Any], state: ConversationState, model_id: str) -> str:
    latency = metrics.get('latency', 0)
    inp = metrics.get('input_tokens', 0)
    out = metrics.get('output_tokens', 0)
    total = inp + out
    tps = metrics.get('tps', 0)
    cost = estimate_cost(model_id, inp, out)

    state.stats.total_requests += 1
    state.stats.total_input_tokens += inp
    state.stats.total_output_tokens += out
    state.stats.total_latency += latency
    state.stats.total_cost_vnd += cost
    state.stats.last_active = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _save_state()

    budget_warn = check_budget_warning(state)
    budget_line = f"\n• 🚨 {budget_warn}" if budget_warn else ""

    return (
        f"\n\n{'━' * 22}\n"
        f"📊 Metrics — {get_model_display(state.mode, model_id)}\n"
        f"• ⏱ Latency: `{latency:.2f}s`\n"
        f"• 📝 Input: `{inp:,}` tok\n"
        f"• 💬 Output: `{out:,}` tok\n"
        f"• 📦 Total: `{total:,}` tok\n"
        f"• ⚡ Speed: `{tps:.1f}` tok/s\n"
        f"• 💰 Cost: `{format_vnd(cost)}` VND"
        f"{budget_line}"
    )

async def auto_summarize_history(state: ConversationState):
    if len(state.history) >= AUTO_SUMMARIZE_THRESHOLD * 2:
        # Keep last 8 exchanges, summarize the rest
        to_summarize = state.history[:-(8 * 2)]
        keep = state.history[-(8 * 2):]
        summary_text = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in to_summarize])
        state.context_summary = f"[Summary of {len(to_summarize)} messages] {summary_text[:500]}..."
        state.history = keep
        branch = state.branches.get(state.current_branch_id)
        if branch:
            branch.messages = keep
        _save_state()

# ============================ GITHUB API CLIENT ============================

class GitHubAgent:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def _request(self, method: str, endpoint: str, **kwargs) -> Tuple[int, Any, Dict]:
        await self.init_session()
        url = f"{GITHUB_API_BASE}{endpoint}"
        async with self.session.request(method, url, headers=self.headers, **kwargs) as resp:
            self.rate_limit_remaining = int(resp.headers.get('X-RateLimit-Remaining', 0))
            self.rate_limit_reset = int(resp.headers.get('X-RateLimit-Reset', 0))
            try:
                data = await resp.json()
            except:
                data = await resp.text()
            return resp.status, data, dict(resp.headers)

    async def get_user(self) -> Tuple[bool, Dict]:
        status, data, _ = await self._request("GET", "/user")
        return status == 200, data

    async def create_repo(self, name: str, description: str = "", private: bool = False,
                         auto_init: bool = True, gitignore_template: str = "Python") -> Tuple[bool, Dict]:
        payload = {
            "name": name, "description": description, "private": private,
            "auto_init": auto_init, "gitignore_template": gitignore_template
        }
        status, data, _ = await self._request("POST", "/user/repos", json=payload)
        return status == 201, data

    async def get_repo(self, owner: str, repo: str) -> Tuple[bool, Dict]:
        status, data, _ = await self._request("GET", f"/repos/{owner}/{repo}")
        return status == 200, data

    async def create_file(self, owner: str, repo: str, path: str, content: str,
                         message: str, branch: str = "main") -> Tuple[bool, Dict]:
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        payload = {"message": message, "content": encoded, "branch": branch}
        status, data, _ = await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
        return status in (200, 201), data

    async def get_file(self, owner: str, repo: str, path: str, branch: str = "main") -> Tuple[bool, Dict]:
        status, data, _ = await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
        return status == 200, data

    async def update_file(self, owner: str, repo: str, path: str, content: str,
                           message: str, sha: str, branch: str = "main") -> Tuple[bool, Dict]:
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        payload = {"message": message, "content": encoded, "sha": sha, "branch": branch}
        status, data, _ = await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
        return status in (200, 201), data

    async def delete_file(self, owner: str, repo: str, path: str, message: str,
                           sha: str, branch: str = "main") -> Tuple[bool, Dict]:
        payload = {"message": message, "sha": sha, "branch": branch}
        status, data, _ = await self._request("DELETE", f"/repos/{owner}/{repo}/contents/{path}", json=payload)
        return status == 200, data

    async def list_files(self, owner: str, repo: str, path: str = "", branch: str = "main") -> Tuple[bool, List]:
        endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={branch}" if path else f"/repos/{owner}/{repo}/contents?ref={branch}"
        status, data, _ = await self._request("GET", endpoint)
        if status == 200 and isinstance(data, list):
            return True, data
        return False, data if isinstance(data, list) else []

    async def create_branch(self, owner: str, repo: str, new_branch: str, from_branch: str = "main") -> Tuple[bool, Dict]:
        status, data, _ = await self._request("GET", f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}")
        if status != 200:
            return False, data
        sha = data.get("object", {}).get("sha", "")
        payload = {"ref": f"refs/heads/{new_branch}", "sha": sha}
        status, data, _ = await self._request("POST", f"/repos/{owner}/{repo}/git/refs", json=payload)
        return status == 201, data

    async def create_pr(self, owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> Tuple[bool, Dict]:
        payload = {"title": title, "head": head, "base": base, "body": body}
        status, data, _ = await self._request("POST", f"/repos/{owner}/{repo}/pulls", json=payload)
        return status == 201, data

    async def get_commits(self, owner: str, repo: str, branch: str = "main", per_page: int = 10) -> Tuple[bool, List]:
        status, data, _ = await self._request("GET", f"/repos/{owner}/{repo}/commits?sha={branch}&per_page={per_page}")
        if status == 200 and isinstance(data, list):
            return True, data
        return False, []

    async def create_issue(self, owner: str, repo: str, title: str, body: str = "",
                          labels: List[str] = None) -> Tuple[bool, Dict]:
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        status, data, _ = await self._request("POST", f"/repos/{owner}/{repo}/issues", json=payload)
        return status == 201, data

    async def create_release(self, owner: str, repo: str, tag: str, name: str,
                              body: str = "", draft: bool = False, prerelease: bool = False) -> Tuple[bool, Dict]:
        payload = {"tag_name": tag, "name": name, "body": body, "draft": draft, "prerelease": prerelease}
        status, data, _ = await self._request("POST", f"/repos/{owner}/{repo}/releases", json=payload)
        return status == 201, data

    async def list_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 10) -> Tuple[bool, List]:
        status, data, _ = await self._request("GET", f"/repos/{owner}/{repo}/issues?state={state}&per_page={per_page}")
        if status == 200 and isinstance(data, list):
            return True, data
        return False, []

    async def create_workflow(self, owner: str, repo: str, name: str, content: str) -> Tuple[bool, Dict]:
        path = f".github/workflows/{name}.yml"
        return await self.create_file(owner, repo, path, content, f"Add CI workflow {name}")

    async def get_readme(self, owner: str, repo: str) -> Tuple[bool, str]:
        status, data, _ = await self._request("GET", f"/repos/{owner}/{repo}/readme")
        if status == 200 and isinstance(data, dict):
            content = data.get("content", "")
            try:
                decoded = base64.b64decode(content.replace("\n", "")).decode('utf-8')
                return True, decoded
            except:
                return True, content
        return False, ""

    async def fork_repo(self, owner: str, repo: str) -> Tuple[bool, Dict]:
        status, data, _ = await self._request("POST", f"/repos/{owner}/{repo}/forks")
        return status == 202, data

    async def star_repo(self, owner: str, repo: str) -> Tuple[bool, Dict]:
        status, data, _ = await self._request("PUT", f"/user/starred/{owner}/{repo}")
        return status == 204, data

    async def search_repos(self, query: str, per_page: int = 10) -> Tuple[bool, List]:
        status, data, _ = await self._request("GET", f"/search/repositories?q={query}&per_page={per_page}")
        if status == 200 and isinstance(data, dict):
            return True, data.get("items", [])
        return False, []

    async def get_rate_limit(self) -> Tuple[bool, Dict]:
        status, data, _ = await self._request("GET", "/rate_limit")
        return status == 200, data

github_agent = GitHubAgent(GITHUB_TOKEN)

# ============================ AI API CLIENTS ============================

async def call_chat_api(
    session: aiohttp.ClientSession,
    model_id: str,
    messages: List[Dict[str, str]],
    status_msg: Any,
    system_prompt: str = SYSTEM_PROMPT,
    max_tokens: int = MAX_OUTPUT_TOKENS,
    temperature: float = 0.7,
) -> Tuple[str, Dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    msgs = []
    has_system = False
    for m in messages:
        if m.get("role") == "system":
            if not has_system:
                msgs.append({"role": "system", "content": system_prompt})
                has_system = True
        else:
            msgs.append(m)
    if not has_system:
        msgs.insert(0, {"role": "system", "content": system_prompt})

    payload = {
        "model": model_id,
        "messages": msgs,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    start_time = time.time()
    dots = 0

    async def _update_status():
        nonlocal dots
        while True:
            try:
                await asyncio.sleep(STATUS_UPDATE_INTERVAL)
                elapsed = time.time() - start_time
                dots = (dots + 1) % 4
                status_text = (
                    f"⏳ Dang suy nghi{chr(183) * dots}{' ' * (3-dots)}\n\n"
                    f"🤖 Model: `{model_id}`\n"
                    f"⏱ Thoi gian: `{elapsed:.1f}s`\n"
                    f"💡 Trang thai: `Dang tao phan hoi...`"
                )
                await status_msg.edit_text(status_text, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                pass

    status_task = asyncio.create_task(_update_status())

    try:
        timeout = aiohttp.ClientTimeout(total=None, connect=30, sock_read=300)
        async with session.post(API_CHAT_URL, headers=headers, json=payload, timeout=timeout) as resp:
            if resp.status != 200:
                error_body = await resp.text()
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history, status=resp.status,
                    message=f"API Error {resp.status}: {error_body[:500]}"
                )
            result = await resp.json()
    except Exception:
        raise
    finally:
        status_task.cancel()
        try:
            await status_task
        except asyncio.CancelledError:
            pass

    latency = time.time() - start_time

    if not isinstance(result, dict):
        raise ValueError(f"Invalid API response type: {type(result)}")

    choices = result.get('choices', [])
    if not choices:
        raise ValueError("No choices in API response")

    content = choices[0].get('message', {}).get('content', '')
    if not content:
        raise ValueError("Empty content from API")

    usage = result.get('usage', {})
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)

    if input_tokens == 0:
        input_tokens = sum(estimate_tokens(m.get('content', '')) for m in msgs)
    if output_tokens == 0:
        output_tokens = estimate_tokens(content)

    metrics = {
        'latency': latency,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'tps': output_tokens / latency if latency > 0 else 0
    }

    return content, metrics

async def call_embed_api(
    session: aiohttp.ClientSession,
    model_id: str,
    text_input: str,
    status_msg: Any,
) -> Tuple[str, Dict[str, Any], str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {"model": model_id, "input": text_input}

    start_time = time.time()
    dots = 0

    async def _update_status():
        nonlocal dots
        while True:
            try:
                await asyncio.sleep(STATUS_UPDATE_INTERVAL)
                elapsed = time.time() - start_time
                dots = (dots + 1) % 4
                await status_msg.edit_text(
                    f"⏳ Dang embed{chr(183) * dots}{' ' * (3-dots)}\n\n"
                    f"🤖 Model: `{model_id}`\n"
                    f"⏱ Thoi gian: `{elapsed:.1f}s`\n"
                    f"💡 Trang thai: `Dang tinh vector...`",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass

    status_task = asyncio.create_task(_update_status())

    try:
        timeout = aiohttp.ClientTimeout(total=None, connect=30)
        async with session.post(API_EMBED_URL, headers=headers, json=payload, timeout=timeout) as resp:
            if resp.status != 200:
                error_body = await resp.text()
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history, status=resp.status,
                    message=f"API Error {resp.status}: {error_body[:500]}"
                )
            result = await resp.json()
    finally:
        status_task.cancel()
        try:
            await status_task
        except asyncio.CancelledError:
            pass

    latency = time.time() - start_time

    data = result.get('data', [])
    if not data:
        raise ValueError("No embedding data returned")

    embedding = data[0].get('embedding', [])
    dims = len(embedding)
    preview = embedding[:5]
    preview_str = ", ".join([f"{v:.6f}" for v in preview])

    content = (
        f"📊 Embedding Result\n"
        f"{'━' * 20}\n"
        f"• 📐 Dimensions: `{dims}`\n"
        f"• 🔢 Preview: `{preview_str}...`\n\n"
        f"📄 Full vector da duoc luu trong file dinh kem."
    )

    full_vector_text = f"Model: {model_id}\nDimensions: {dims}\n\nEmbedding Vector:\n{json.dumps(embedding, indent=2)}"

    usage = result.get('usage', {})
    input_tokens = usage.get('prompt_tokens', 0) or usage.get('input_tokens', 0) or estimate_tokens(text_input)

    metrics = {
        'latency': latency,
        'input_tokens': input_tokens,
        'output_tokens': 0,
        'total_tokens': input_tokens,
        'tps': 0
    }

    return content, metrics, full_vector_text

async def call_tts_api(
    session: aiohttp.ClientSession,
    model_id: str,
    text_input: str,
    status_msg: Any,
) -> Tuple[bytes, Dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": model_id,
        "input": text_input,
        "voice": "alloy"
    }

    start_time = time.time()
    dots = 0

    async def _update_status():
        nonlocal dots
        while True:
            try:
                await asyncio.sleep(STATUS_UPDATE_INTERVAL)
                elapsed = time.time() - start_time
                dots = (dots + 1) % 4
                await status_msg.edit_text(
                    f"⏳ Dang tong hop giong noi{chr(183) * dots}{' ' * (3-dots)}\n\n"
                    f"🤖 Model: `{model_id}`\n"
                    f"⏱ Thoi gian: `{elapsed:.1f}s`\n"
                    f"💡 Trang thai: `Dang tao audio...`",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception:
                pass

    status_task = asyncio.create_task(_update_status())

    try:
        timeout = aiohttp.ClientTimeout(total=None, connect=30)
        async with session.post(API_TTS_URL, headers=headers, json=payload, timeout=timeout) as resp:
            if resp.status != 200:
                error_body = await resp.text()
                raise aiohttp.ClientResponseError(
                    resp.request_info, resp.history, status=resp.status,
                    message=f"API Error {resp.status}: {error_body[:500]}"
                )
            audio_bytes = await resp.read()
    finally:
        status_task.cancel()
        try:
            await status_task
        except asyncio.CancelledError:
            pass

    latency = time.time() - start_time

    if not audio_bytes or len(audio_bytes) < 100:
        raise ValueError("Received empty or invalid audio data")

    metrics = {
        'latency': latency,
        'input_tokens': estimate_tokens(text_input),
        'output_tokens': 0,
        'total_tokens': estimate_tokens(text_input),
        'tps': 0
    }

    return audio_bytes, metrics

async def call_image_api(
    session: aiohttp.ClientSession,
    prompt: str,
    model: str = "thanhnhan9023/gpt-image-2",
    size: str = "1024x1024",
    status_msg: Any = None,
) -> Tuple[bytes, str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size
    }

    start_time = time.time()

    if status_msg:
        await status_msg.edit_text("🎨 Dang tao hinh anh...", parse_mode=ParseMode.MARKDOWN)

    timeout = aiohttp.ClientTimeout(total=120, connect=30)
    async with session.post(API_IMAGE_URL, headers=headers, json=payload, timeout=timeout) as resp:
        if resp.status != 200:
            error_body = await resp.text()
            raise Exception(f"Image API Error {resp.status}: {error_body[:500]}")
        result = await resp.json()

    latency = time.time() - start_time

    data = result.get('data', [])
    if not data:
        raise ValueError("No image data returned")

    image_url = data[0].get('url', '')
    if not image_url:
        b64 = data[0].get('b64_json', '')
        if b64:
            return base64.b64decode(b64), f"Generated in {latency:.1f}s"
        raise ValueError("No image URL or base64 returned")

    async with session.get(image_url) as img_resp:
        image_bytes = await img_resp.read()

    return image_bytes, f"Generated in {latency:.1f}s"

# ============================ WEB SEARCH (REAL DUCKDUCKGO) ============================

async def web_search(session: aiohttp.ClientSession, query: str, num_results: int = 5) -> List[Dict[str, str]]:
    try:
        url = f"https://html.duckduckgo.com/html/?q={aiohttp.helpers.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                html_text = await resp.text()
                results = []
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_text, 'html.parser')
                    for result in soup.find_all('div', class_='result')[:num_results]:
                        a = result.find('a', class_='result__a')
                        snippet = result.find('a', class_='result__snippet')
                        if a and snippet:
                            results.append({
                                "title": a.get_text(strip=True),
                                "url": a.get('href', ''),
                                "snippet": snippet.get_text(strip=True)[:200]
                            })
                except Exception:
                    pass
                if results:
                    return results
    except Exception as e:
        logger.warning(f"Web search error: {e}")
    return [
        {"title": f"Result {i+1} for: {query[:40]}", "url": "https://duckduckgo.com", "snippet": "Search result..."}
        for i in range(num_results)
    ]

async def fetch_webpage(session: aiohttp.ClientSession, url: str) -> str:
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(url, timeout=timeout, headers={"User-Agent": "DeniaBot/1.0"}) as resp:
            if resp.status == 200:
                html = await resp.text()
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    text = soup.get_text(separator=' ', strip=True)
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    return text[:8000]
                except Exception:
                    text = re.sub(r'<[^>]+>', ' ', html)
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text[:5000]
            return f"Error: HTTP {resp.status}"
    except Exception as e:
        return f"Error fetching page: {str(e)}"

# ============================ CODE INTERPRETER (ENHANCED) ============================

class CodeInterpreter:
    BLACKLIST = [
        'import os', 'import sys', 'import subprocess', 'import socket',
        '__import__', 'eval(', 'exec(', 'compile(', 'open(', 'file(',
        'os.system', 'os.popen', 'subprocess.call', 'subprocess.run',
        'import urllib', 'import requests', 'import ftplib',
        'shutil.rmtree', 'os.remove', 'os.unlink', 'os.rmdir',
        'import pathlib', 'pathlib.Path', 'import pickle'
    ]

    @staticmethod
    async def execute(code: str, timeout: int = 30) -> Tuple[bool, str, str]:
        code_lower = code.lower()
        for banned in CodeInterpreter.BLACKLIST:
            if banned.lower() in code_lower:
                return False, "", f"Security Error: Forbidden pattern '{banned}' detected"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024*1024
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                success = proc.returncode == 0
                return success, stdout.decode('utf-8', errors='replace')[:8000], stderr.decode('utf-8', errors='replace')[:4000]
            except asyncio.TimeoutError:
                proc.kill()
                return False, "", f"Execution timeout after {timeout}s"
        except Exception as e:
            return False, "", f"Execution error: {str(e)}"
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    @staticmethod
    async def execute_with_matplotlib(code: str, timeout: int = 30) -> Tuple[bool, str, str, Optional[bytes]]:
        code_lower = code.lower()
        for banned in CodeInterpreter.BLACKLIST:
            if banned.lower() in code_lower:
                return False, "", f"Security Error: Forbidden pattern '{banned}' detected", None
        wrapped = """import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io

""" + code + """
figs = [plt.figure(i) for i in plt.get_fignums()]
if figs:
    buf = io.BytesIO()
    figs[-1].savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    print("__PLOT__" + img_b64)
    plt.close('all')
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapped)
            temp_path = f.name
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024*1024
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                out_text = stdout.decode('utf-8', errors='replace')[:8000]
                err_text = stderr.decode('utf-8', errors='replace')[:4000]
                success = proc.returncode == 0
                img_bytes = None
                if "__PLOT__" in out_text:
                    parts = out_text.split("__PLOT__")
                    out_text = parts[0].strip()
                    try:
                        img_bytes = base64.b64decode(parts[1].strip().split('\n')[0])
                    except:
                        pass
                return success, out_text, err_text, img_bytes
            except asyncio.TimeoutError:
                proc.kill()
                return False, "", f"Execution timeout after {timeout}s", None
        except Exception as e:
            return False, "", f"Execution error: {str(e)}", None
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

# ============================ AGENT INTELLIGENCE ============================

async def agent_self_reflect(task: AgentTask, state: ConversationState) -> str:
    reflection = (
        f"🧠 Self-Reflection\n"
        f"{'━' * 20}\n"
        f"• Task: `{task.task_id}`\n"
        f"• Status: {task.status}\n"
    )
    if task.error:
        reflection += f"• Error recorded: `{task.error[:100]}`\n"
        state.self_notes.append(f"Avoid [{datetime.now().strftime('%H:%M')}]: {task.error[:200]}")
    else:
        reflection += f"• Success pattern recorded\n"
        state.self_notes.append(f"Success [{datetime.now().strftime('%H:%M')}]: {task.description[:200]}")
    state.self_notes = state.self_notes[-100:]
    _save_state()
    return reflection

async def agent_analyze_code(code: str, language: str = "python") -> Dict[str, Any]:
    issues = []
    warnings = []
    info = []
    score = 100
    if language == "python":
        try:
            compile(code, '<string>', 'exec')
            info.append("✅ Syntax: Valid Python")
        except SyntaxError as e:
            issues.append(f"❌ Syntax Error: Line {e.lineno}: {e.msg}")
            score -= 30
        dangerous_patterns = [
            (r'eval\s*\(', "Dangerous eval() detected"),
            (r'exec\s*\(', "Dangerous exec() detected"),
            (r'input\s*\(.*\)', "Potential injection vulnerability"),
            (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "Shell=True is dangerous"),
            (r'os\.system\s*\(', "os.system() is dangerous"),
            (r'pickle\.loads?\s*\(', "Unsafe pickle usage"),
            (r'yaml\.load\s*\([^)]*Loader\s*=\s*None', "Unsafe YAML loading"),
        ]
        for pattern, msg in dangerous_patterns:
            if re.search(pattern, code):
                issues.append(f"🔒 {msg}")
                score -= 25
        if "import *" in code:
            warnings.append("⚠️ Wildcard imports detected")
            score -= 5
        if "except:" in code and "except Exception" not in code:
            warnings.append("⚠️ Bare except: found")
            score -= 5
        if "print(" in code and "logging" not in code and len(code.split('\n')) > 30:
            warnings.append("💡 Consider using logging instead of print()")
            score -= 3
        if "TODO" in code or "FIXME" in code:
            warnings.append("📝 TODO/FIXME markers found")
            score -= 2
        if code.count('def ') > 20:
            warnings.append("📊 High function count")
            score -= 3
        if 'if __name__ ==' not in code and len(code.split('\n')) > 25:
            warnings.append("⚠️ No __main__ guard")
            score -= 3
        if 'typing' not in code and len(code.split('\n')) > 50:
            warnings.append("💡 Consider adding type hints")
            score -= 2
        dq = chr(34) * 3
        sq = chr(39) * 3
        if dq not in code and sq not in code and len(code.split('\n')) > 30:
            warnings.append("💡 Missing docstrings")
            score -= 3
        lines = len(code.split('\n'))
        if lines > 500:
            warnings.append(f"📊 Large file: {lines} lines")
            score -= 5
        async_count = len(re.findall(r'\basync def\b', code))
        await_count = len(re.findall(r'\bawait\b', code))
        if async_count > 0 and await_count == 0:
            warnings.append("⚠️ async functions without await")
            score -= 5
    return {
        "score": max(0, score),
        "issues": issues,
        "warnings": warnings,
        "info": info,
        "language": language,
        "lines": len(code.split('\n'))
    }

def generate_dockerfile(project_type: str = "python", requirements: List[str] = None) -> str:
    if project_type == "python":
        return """FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"
EXPOSE 8000
CMD ["python", "main.py"]
"""
    elif project_type == "node":
        return """FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
USER node
EXPOSE 3000
CMD ["node", "index.js"]
"""
    elif project_type == "go":
        return """FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .
FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE 8080
CMD ["./main"]
"""
    elif project_type == "rust":
        return """FROM rust:1.75-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y libssl-dev && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/target/release/app /usr/local/bin/app
EXPOSE 8080
CMD ["app"]
"""
    else:
        return "# Dockerfile template\nFROM alpine:latest\nWORKDIR /app\nCOPY . .\nCMD [\"echo\", \"Hello World\"]\n"

def generate_github_actions(project_type: str = "python") -> str:
    if project_type == "python":
        return """name: CI/CD Pipeline
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 black
    - name: Lint with flake8
      run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    - name: Format check with black
      run: black --check .
    - name: Test with pytest
      run: pytest --cov=./ --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run Bandit security scan
      uses: PyCQA/bandit@main
      with:
        args: "-r . -f json -o bandit-report.json || true"
    - name: Upload security report
      uses: actions/upload-artifact@v3
      with:
        name: security-report
        path: bandit-report.json
"""
    elif project_type == "node":
        return """name: Node.js CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18.x, 20.x]
    steps:
    - uses: actions/checkout@v4
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    - run: npm ci
    - run: npm run build --if-present
    - run: npm test
"""
    else:
        return "# GitHub Actions template\nname: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: echo \"Build\"\n"

# ============================ KNOWLEDGE BASE (RAG) ============================

class SimpleRAG:
    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    @staticmethod
    async def query_knowledge_base(
        session: aiohttp.ClientSession,
        query: str,
        documents: List[KnowledgeDocument],
        embed_model: str = "text-embedding-3-small",
        top_k: int = 3
    ) -> List[Tuple[str, float, str]]:
        if not documents:
            return []
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        payload = {"model": embed_model, "input": query}
        async with session.post(API_EMBED_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                return []
            result = await resp.json()
        query_embedding = result.get('data', [{}])[0].get('embedding', [])
        if not query_embedding:
            return []
        results = []
        for doc in documents:
            if doc.embedding:
                score = SimpleRAG.cosine_similarity(query_embedding, doc.embedding)
                if score > 0.5:
                    results.append((doc.filename, score, doc.content[:1000]))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

# ============================ CODE FORMATTER ============================

class CodeFormatter:
    @staticmethod
    async def format_python(code: str) -> Tuple[bool, str, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "black", "-", "--quiet",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(code.encode()), timeout=10)
            if proc.returncode == 0:
                return True, stdout.decode('utf-8'), ""
            return False, code, stderr.decode('utf-8', errors='replace')[:500]
        except Exception as e:
            return False, code, str(e)

    @staticmethod
    def format_json(data: Any) -> str:
        try:
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        except:
            return str(data)

    @staticmethod
    def format_diff(old: str, new: str) -> str:
        import difflib
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        return ''.join(diff)[:4000]

# ============================ COMMAND HANDLERS ============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    mode_name = MODE_CONFIG[state.mode]["name"]
    model_disp = get_model_display(state.mode, state.current_model)
    welcome = (
        f"╔══════════════════════════╗\n"
        f"║     🤖 DENIA BOT v6.0    ║\n"
        f"║   ULTIMATE AI PLATFORM   ║\n"
        f"╚══════════════════════════╝\n\n"
        f"👋 Chao mung *{escape_markdown(update.effective_user.first_name or 'ban')}*!\n\n"
        f"🧠 AI Agent Tu Chu — Code · Hoc · Cai Thien\n\n"
        f"📦 7 Che do thong minh:\n"
        f"• 💬 Chat — Hoi dap da mo hinh\n"
        f"• 🤖 Agent — Tu dong code & push GitHub\n"
        f"• 💻 Coder — Chuyen gia lap trinh\n"
        f"• 📚 Lesson — Hoc lap trinh 2000 bai/ngon ngu\n"
        f"• 📊 Embed — Text → Vector AI\n"
        f"• 🔊 TTS — Giong noi tu nhien\n"
        f"• 👁 Vision — Phan tich hinh anh\n\n"
        f"🚀 Hien tai: {mode_name} | {model_disp}\n\n"
        f"📚 Lenh chinh:\n"
        f"• /models — Chon model (98+ models)"
        f"• /mode — Doi che do\n"
        f"• /agent — Chay agent tu chu (co chon model)"
        f"• /agent_advanced — Agent nang cao\n"
        f"• /git — GitHub full control\n"
        f"• /lesson — Hoc lap trinh\n"
        f"• /leetcode — Luyen LeetCode\n"
        f"• /kb — Knowledge Base (RAG)\n"
        f"• /run — Chay code Python + Matplotlib\n"
        f"• /search — Tim kiem web thuc\n"
        f"• /image — Tao anh AI\n"
        f"• /format — Format code\n"
        f"• /snippet — Quan ly code snippets\n"
        f"• /whiteboard — Bang trang\n"
        f"• /docker — Tao Dockerfile\n"
        f"• /cicd — Tao GitHub Actions\n"
        f"• /analyze — Phan tich code\n"
        f"• /diff — So sanh code\n"
        f"• /branch — Quan ly nhanh chat\n"
        f"• /remind — Hen gio nhac nho\n"
        f"• /settings — Tuy chinh ca nhan\n"
        f"• /status — Trang thai & chi phi\n"
        f"• /stats — Thong ke chi tiet\n"
        f"• /reset — Xoa ngu canh\n"
        f"• /help — Chi tiet day du"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"📖 Huong Dan Day Du — Denia Bot v6.0\n"
        f"{'━' * 26}\n\n"
        f"🚀 Lenh Co Ban:\n"
        f"• /start — Khoi dong bot\n"
        f"• /models — Danh sach 98+ model\n"
        f"• /switch <so> — Doi model nhanh\n"
        f"• /mode — Doi che do chat/agent/coder/lesson/embed/tts/vision\n"
        f"• /status — Trang thai & chi phi\n"
        f"• /stats — Thong ke su dung\n"
        f"• /reset — Xoa lich su + ngu canh\n"
        f"• /settings — Tuy chinh ngon ngu, style, verbosity, dinh dang file, gioi han chi phi\n"
        f"• /export — Xuat du lieu\n"
        f"• /import — Nhap du lieu (reply file JSON)\n\n"
        f"🤖 Agent & Code:\n"
        f"• /agent <mo ta> — Agent tu code & push GitHub (chon model truoc)\n"
        f"• /agent_advanced <mo ta> — Agent voi review + test + docs + Docker + CI/CD\n"
        f"• /git — Danh sach lenh GitHub\n"
        f"  - /git repo <ten> [desc] [private] — Tao repo\n"
        f"  - /git push <o/r> <path> — Push file\n"
        f"  - /git get <o/r> <path> — Doc file\n"
        f"  - /git list <o/r> [path] — Liet ke\n"
        f"  - /git update <o/r> <path> — Update\n"
        f"  - /git delete <o/r> <path> — Xoa\n"
        f"  - /git branch <o/r> <branch> — Tao branch\n"
        f"  - /git pr <o/r> <title> <head> <base> — Tao PR\n"
        f"  - /git issue <o/r> <title> — Tao issue\n"
        f"  - /git release <o/r> <tag> — Tao release\n"
        f"  - /git workflow <o/r> <name> — Tao CI workflow\n"
        f"  - /git commits <o/r> — Xem lich su\n"
        f"  - /git search <query> — Tim repo\n"
        f"  - /git fork <o/r> — Fork repo\n"
        f"  - /git star <o/r> — Star repo\n"
        f"• /analyze — Phan tich code (reply code)\n"
        f"• /run <code> — Chay Python sandbox\n"
        f"• /runplot <code> — Chay Python + Matplotlib\n"
        f"• /docker <type> — Tao Dockerfile\n"
        f"• /cicd <type> — Tao GitHub Actions\n"
        f"• /diff <code1> | <code2> — So sanh code\n"
        f"• /testgen <code> — Tao unit test\n"
        f"• /format — Format code Python (reply code)\n"
        f"• /snippet save <ten> — Luu snippet\n"
        f"• /snippet list — Xem snippets\n"
        f"• /snippet get <ten> — Lay snippet\n"
        f"• /snippet delete <ten> — Xoa snippet\n\n"
        f"📚 Learning:\n"
        f"• /lesson — Bat dau hoc lap trinh\n"
        f"• /lesson_lang <ngon ngu> — Chon ngon ngu hoc\n"
        f"• /lesson_next — Bai tiep theo\n"
        f"• /leetcode — Luyen LeetCode\n"
        f"• /leetcode_topic <chu de> — Chon chu de\n"
        f"• /leetcode_diff <easy/medium/hard> — Chon do kho\n\n"
        f"🧠 Knowledge & Search:\n"
        f"• /kb upload — Upload file (reply file)\n"
        f"• /kb ask <cau hoi> — Hoi dua tren KB\n"
        f"• /kb list — Xem tai lieu da upload\n"
        f"• /kb clear — Xoa toan bo KB\n"
        f"• /search <query> — Tim kiem web thuc (DuckDuckGo)\n"
        f"• /fetch <url> — Lay noi dung web\n\n"
        f"🎨 Multimedia:\n"
        f"• /image <mo ta> — Tao anh AI\n"
        f"• /tts <van ban> — Text → Giong noi\n"
        f"• /stt — Voice → Text (reply voice)\n"
        f"• /vision — Phan tich anh (reply anh)\n\n"
        f"🌿 Conversation & Memory:\n"
        f"• /branch — Quan ly nhanh chat\n"
        f"  - /branch new <ten> — Tao nhanh moi\n"
        f"  - /branch switch <id> — Chuyen nhanh\n"
        f"  - /branch list — Liet ke\n"
        f"  - /branch merge <id> — Gop nhanh\n"
        f"• /remind <time> <message> — Hen gio\n"
        f"  - /remind 10m uong nuoc\n"
        f"  - /remind 2h bao cao\n"
        f"• /persona <mo ta> — Dat tinh cach AI\n"
        f"• /whiteboard — Bang trang tu do\n"
        f"  - /whiteboard add <noi dung> — Them\n"
        f"  - /whiteboard clear — Xoa\n"
        f"  - /whiteboard show — Xem\n"
        f"• /learn — Xem ghi chu tu hoc\n"
        f"• /tasks — Lich su agent tasks\n\n"
        f"⚠️ Luu y:\n"
        f"• Dung /reset neu AI bi lan ngu canh\n"
        f"• Agent mode can mo ta ro rang\n"
        f"• Code sandbox co gioi han bao mat\n"
        f"• Gia moi model khac nhau — xem /models\n"
        f"• File qua dai se gui theo dinh dang da chon trong /settings"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def show_models(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    mode = state.mode
    mode_name = MODE_CONFIG[mode]["name"]
    current_model = state.current_model
    models_list = MODE_CONFIG[mode]["models"]

    keyboard = []
    row = []
    for idx, (cat, model_id, display, tier, inp, out) in enumerate(models_list, 1):
        prefix = "✅ " if model_id == current_model else ""
        emoji = CATEGORY_EMOJI.get(tier, "⚪")
        btn_text = f"{prefix}{idx}.{emoji}{display[:22]}"
        button = InlineKeyboardButton(btn_text, callback_data=f"model_{mode}_{idx}")
        row.append(button)
        if len(row) == 1:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton("💚 Free", callback_data="filter_Free"),
        InlineKeyboardButton("💛 Low", callback_data="filter_Low"),
        InlineKeyboardButton("🧡 Mid", callback_data="filter_Mid"),
        InlineKeyboardButton("❤️ High+", callback_data="filter_High"),
    ])
    keyboard.append([InlineKeyboardButton("🔄 Lam moi", callback_data="refresh_models")])

    header = (
        f"📂 Danh Sach Model — {mode_name}\n"
        f"{'━' * 24}\n"
        f"✅ = Dang dung: `{get_model_display(mode, current_model)}`\n"
        f"📊 Tong: {len(models_list)} models\n"
        f"💚Free 💛Low 🧡Mid ❤️High+ 💜Special\n\n"
        f"👇 Chon model:"
    )
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    data = query.data

    if data == "refresh_models":
        await query.edit_message_text("🔄 Dang lam moi...")
        await show_models(update, context)
        return

    if data.startswith("filter_"):
        tier = data.replace("filter_", "")
        mode = state.mode
        models_list = MODE_CONFIG[mode]["models"]
        filtered = [m for m in models_list if m[3] == tier]
        if not filtered:
            await query.edit_message_text(f"❌ Khong co model {tier}.", parse_mode=ParseMode.MARKDOWN)
            return
        keyboard = []
        row = []
        for idx, (cat, model_id, display, t, inp, out) in enumerate(filtered, 1):
            prefix = "✅ " if model_id == state.current_model else ""
            emoji = CATEGORY_EMOJI.get(tier, "⚪")
            btn_text = f"{prefix}{idx}.{emoji}{display[:22]}"
            orig_idx = models_list.index((cat, model_id, display, t, inp, out)) + 1
            row.append(InlineKeyboardButton(btn_text, callback_data=f"model_{mode}_{orig_idx}"))
            if len(row) == 1:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("⬅️ Quay lai", callback_data="refresh_models")])
        await query.edit_message_text(
            f"📂 Model {tier} — {len(filtered)} models\n👇 Chon:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("model_"):
        parts = data.split("_")
        if len(parts) >= 3:
            mode = parts[1]
            try:
                choice = int(parts[2])
                models_list = MODE_CONFIG[mode]["models"]
                if 1 <= choice <= len(models_list):
                    cat, selected_id, selected_disp, tier, inp, out = models_list[choice - 1]
                    state.mode = mode
                    state.current_model = selected_id
                    state.last_model_warning = get_model_cost_warning(selected_id)
                    _save_state()
                    await query.edit_message_text(
                        f"✅ Da chuyen!\n\n"
                        f"🔄 Mode: *{MODE_CONFIG[mode]['name']}*\n"
                        f"🤖 Model: *{CATEGORY_EMOJI.get(tier, '⚪')} {selected_disp.split(' (')[0]}*\n"
                        f"💰 Gia: `{inp}`/`{out}` VND/1M tok\n"
                        f"🆔 ID: `{selected_id}`\n\n"
                        f"💡 Go /reset neu muon xoa ngu canh cu.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await query.edit_message_text("❌ So khong hop le.", parse_mode=ParseMode.MARKDOWN)
            except ValueError:
                await query.edit_message_text("❌ Loi xu ly.", parse_mode=ParseMode.MARKDOWN)

async def switch_model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Cu phap: /switch <so>\nVi du: /switch 2", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        choice = int(context.args[0])
        user_id = update.effective_user.id
        state = await get_user_state(user_id)
        mode = state.mode
        models_list = MODE_CONFIG[mode]["models"]
        if 1 <= choice <= len(models_list):
            cat, selected_id, selected_disp, tier, inp, out = models_list[choice - 1]
            state.current_model = selected_id
            state.last_model_warning = get_model_cost_warning(selected_id)
            _save_state()
            await update.message.reply_text(
                f"✅ Da chuyen model!\n\n"
                f"🤖 {CATEGORY_EMOJI.get(tier, '⚪')} *{selected_disp.split(' (')[0]}*\n"
                f"💰 `{inp}`/`{out}` VND/1M\n"
                f"🆔 `{selected_id}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(f"❌ Chon so tu 1 den {len(models_list)}.", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("❌ Vui long nhap so hop le.", parse_mode=ParseMode.MARKDOWN)

async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if not context.args:
        current = state.mode
        keyboard = []
        for mode_key, mode_info in MODE_CONFIG.items():
            prefix = "✅ " if mode_key == current else ""
            keyboard.append([InlineKeyboardButton(f"{prefix}{mode_info['name']}", callback_data=f"setmode_{mode_key}")])
        await update.message.reply_text(
            f"🔄 Chon che do hoat dong:\nHien tai: {MODE_CONFIG[current]['name']}",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    mode_arg = context.args[0].lower()
    if mode_arg in MODE_CONFIG:
        state.mode = mode_arg
        state.current_model = MODE_CONFIG[mode_arg]["default"]
        state.history = []
        _save_state()
        await update.message.reply_text(
            f"✅ Da chuyen che do!\n\n"
            f"🔄 Mode: *{MODE_CONFIG[mode_arg]['name']}*\n"
            f"🤖 Model mac dinh: `{state.current_model}`\n"
            f"🗑 Da xoa lich su cu.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "❌ Che do khong hop le!\nChon: chat, agent, coder, lesson, embed, tts, vision",
            parse_mode=ParseMode.MARKDOWN
        )

async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    data = query.data
    if data.startswith("setmode_"):
        mode_key = data.replace("setmode_", "")
        if mode_key in MODE_CONFIG:
            state.mode = mode_key
            state.current_model = MODE_CONFIG[mode_key]["default"]
            state.history = []
            _save_state()
            await query.edit_message_text(
                f"✅ Da chuyen che do!\n\n"
                f"🔄 Mode: *{MODE_CONFIG[mode_key]['name']}*\n"
                f"🤖 Model: `{state.current_model}`\n"
                f"🗑 Da xoa lich su cu.",
                parse_mode=ParseMode.MARKDOWN
            )

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_states:
        old_state = user_states[user_id]
        new_state = ConversationState()
        new_state.stats = old_state.stats
        new_state.preferences = old_state.preferences
        new_state.github_username = old_state.github_username
        new_state.self_notes = old_state.self_notes
        new_state.lesson_progress = old_state.lesson_progress
        new_state.snippet_storage = old_state.snippet_storage
        new_state.branches = {"main": ConversationBranch("main", None, "Main Conversation")}
        new_state.current_branch_id = "main"
        user_states[user_id] = new_state
        _save_state()
    await update.message.reply_text(
        "🗑 Da xoa toan bo ngu canh!\n"
        "🆕 History + tasks + branches moi.\n"
        "📊 Stats, preferences, lessons, snippets duoc giu lai.",
        parse_mode=ParseMode.MARKDOWN
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    history_len = len(state.history)
    mode_name = MODE_CONFIG[state.mode]["name"]
    model_disp = get_model_display(state.mode, state.current_model)
    cat = get_model_category(state.mode, state.current_model)
    tier = get_model_tier(state.mode, state.current_model)
    task_count = len(state.agent_tasks)
    completed = sum(1 for t in state.agent_tasks if t.status == "completed")
    failed = sum(1 for t in state.agent_tasks if t.status == "failed")
    running = sum(1 for t in state.agent_tasks if t.status == "running")
    kb_count = len(state.knowledge_base)
    branch_count = len(state.branches)
    lesson_lang = state.preferences.learning_language
    lp = state.lesson_progress.get(lesson_lang)
    lesson_info = f"`{lp.current_lesson}`" if lp else "0"

    status = (
        f"ℹ️ Trang Thai Denia Bot v6.0\n"
        f"{'━' * 24}\n\n"
        f"👤 User: `{user_id}`\n"
        f"🔄 Mode: {mode_name}\n"
        f"🤖 Model: {model_disp}\n"
        f"🏷 Category: `{cat}` | Tier: `{tier}`\n"
        f"🆔 ID: `{state.current_model}`\n"
        f"💬 History: `{history_len // 2}` cap hoi/dap\n"
        f"📝 Tin nhan: `{history_len}/{MAX_HISTORY * 2}`\n"
        f"🌿 Branches: `{branch_count}`\n"
        f"📚 Knowledge Base: `{kb_count}` docs\n"
        f"📖 Lessons ({lesson_lang}): {lesson_info}\n"
        f"🤖 Agent: `{completed}✅ {failed}❌ {running}🔄 {task_count - completed - failed - running}⏳`\n"
        f"🧠 Self-notes: `{len(state.self_notes)}`\n"
        f"💰 Tong chi phi: `{format_vnd(state.stats.total_cost_vnd)}` VND\n"
        f"📅 Bat dau: `{state.stats.first_seen}`\n"
        f"🕐 Hoat dong cuoi: `{state.stats.last_active}`"
    )
    await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    s = state.stats
    avg_latency = s.total_latency / s.total_requests if s.total_requests > 0 else 0
    avg_cost = s.total_cost_vnd / s.total_requests if s.total_requests > 0 else 0
    stats_text = (
        f"📊 Thong Ke Chi Tiet\n"
        f"{'━' * 24}\n\n"
        f"🔢 Requests: `{s.total_requests}`\n"
        f"📝 Input tokens: `{s.total_input_tokens:,}`\n"
        f"💬 Output tokens: `{s.total_output_tokens:,}`\n"
        f"📦 Tong tokens: `{s.total_input_tokens + s.total_output_tokens:,}`\n"
        f"⏱ Tong latency: `{s.total_latency:.2f}s`\n"
        f"⚡ Latency TB: `{avg_latency:.2f}s`\n"
        f"💰 Tong chi phi: `{format_vnd(s.total_cost_vnd)}` VND\n"
        f"💵 Chi phi TB: `{format_vnd(avg_cost)}`/req\n"
        f"✅ Tasks thanh cong: `{s.tasks_completed}`\n"
        f"❌ Tasks that bai: `{s.tasks_failed}`\n"
        f"📖 Lessons hoan thanh: `{s.lessons_completed}`\n"
        f"🏆 LeetCode giai: `{s.leetcode_solved}`\n"
        f"📁 Files da xu ly: `{s.files_processed}`\n"
        f"🐍 Code da chay: `{s.code_executed}`\n"
        f"📅 Bat dau: `{s.first_seen}`\n"
        f"🕐 Cuoi: `{s.last_active}`"
    )
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    prefs = state.preferences
    if not context.args:
        keyboard = [
            [InlineKeyboardButton(f"🌐 Ngon ngu: {prefs.language}", callback_data="set_lang")],
            [InlineKeyboardButton(f"💻 Code style: {prefs.code_style}", callback_data="set_style")],
            [InlineKeyboardButton(f"📢 Verbosity: {prefs.verbosity}", callback_data="set_verb")],
            [InlineKeyboardButton(f"📄 File format: {prefs.file_format}", callback_data="set_format")],
            [InlineKeyboardButton(f"💰 Budget limit: {format_vnd(prefs.budget_limit_vnd)} VND", callback_data="set_budget")],
            [InlineKeyboardButton(f"📚 Learning lang: {prefs.learning_language}", callback_data="set_learn_lang")],
            [InlineKeyboardButton(f"🎚 Level: {prefs.learning_level}", callback_data="set_level")],
            [InlineKeyboardButton(f"⚡ Auto-run: {'Bat' if prefs.auto_execute else 'Tat'}", callback_data="set_auto")],
            [InlineKeyboardButton(f"🔔 Thong bao: {'Bat' if prefs.notifications else 'Tat'}", callback_data="set_notif")],
        ]
        await update.message.reply_text(
            f"⚙️ Cai Dat Ca Nhan\n"
            f"{'━' * 20}\n\n"
            f"👤 User: `{user_id}`\n"
            f"🌐 Ngon ngu: `{prefs.language}`\n"
            f"💻 Code style: `{prefs.code_style}`\n"
            f"📢 Verbosity: `{prefs.verbosity}`\n"
            f"📄 File format: `{prefs.file_format}`\n"
            f"💰 Budget limit: `{format_vnd(prefs.budget_limit_vnd)}` VND\n"
            f"📚 Learning: `{prefs.learning_language}` ({prefs.learning_level})\n"
            f"⚡ Auto-run: `{'Bat' if prefs.auto_execute else 'Tat'}`\n"
            f"🔔 Thong bao: `{'Bat' if prefs.notifications else 'Tat'}`\n\n"
            f"👇 Chon de thay doi:",
            parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    subcmd = context.args[0].lower()
    if subcmd == "lang" and len(context.args) > 1:
        prefs.language = context.args[1]
    elif subcmd == "style" and len(context.args) > 1:
        prefs.code_style = context.args[1]
    elif subcmd == "verbosity" and len(context.args) > 1:
        prefs.verbosity = context.args[1]
    elif subcmd == "format" and len(context.args) > 1:
        fmt = context.args[1].lower()
        if fmt in ("txt", "json", "md", "py"):
            prefs.file_format = fmt
        else:
            await update.message.reply_text("❌ Format: txt, json, md, py", parse_mode=ParseMode.MARKDOWN)
            return
    elif subcmd == "budget" and len(context.args) > 1:
        try:
            prefs.budget_limit_vnd = float(context.args[1])
        except:
            await update.message.reply_text("❌ Nhap so hop le.", parse_mode=ParseMode.MARKDOWN)
            return
    elif subcmd == "learn_lang" and len(context.args) > 1:
        lang = context.args[1].lower()
        if lang in LEARNING_LANGUAGES:
            prefs.learning_language = lang
            if lang not in state.lesson_progress:
                state.lesson_progress[lang] = LessonProgress(lang)
        else:
            langs = ", ".join(LEARNING_LANGUAGES[:10]) + "..."
            await update.message.reply_text(f"❌ Ngon ngu khong ho tro.\n{langs}", parse_mode=ParseMode.MARKDOWN)
            return
    elif subcmd == "level" and len(context.args) > 1:
        lvl = context.args[1].lower()
        if lvl in ("beginner", "intermediate", "advanced"):
            prefs.learning_level = lvl
        else:
            await update.message.reply_text("❌ Level: beginner, intermediate, advanced", parse_mode=ParseMode.MARKDOWN)
            return
    else:
        await update.message.reply_text("❌ Cu phap khong hop le.", parse_mode=ParseMode.MARKDOWN)
        return
    _save_state()
    await update.message.reply_text("✅ Da cap nhat cai dat!", parse_mode=ParseMode.MARKDOWN)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    export_data = {
        "user_id": user_id,
        "exported_at": datetime.now().isoformat(),
        "mode": state.mode,
        "current_model": state.current_model,
        "history": state.history,
        "branches": {bid: {"name": b.name, "messages": b.messages} for bid, b in state.branches.items()},
        "stats": asdict(state.stats),
        "preferences": asdict(state.preferences),
        "agent_tasks": [asdict(t) for t in state.agent_tasks],
        "knowledge_base": [asdict(d) for d in state.knowledge_base],
        "self_notes": state.self_notes,
        "lesson_progress": {k: asdict(v) for k, v in state.lesson_progress.items()},
        "snippet_storage": state.snippet_storage,
        "whiteboard": state.whiteboard,
    }
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
    bio = io.BytesIO(json_str.encode('utf-8'))
    bio.name = f"denia_export_{user_id}_{int(time.time())}.json"
    await update.message.reply_document(
        document=bio,
        caption=f"📤 Xuat Du Lieu\n"
                f"💬 History: `{len(state.history)}` msgs\n"
                f"🌿 Branches: `{len(state.branches)}`\n"
                f"🤖 Tasks: `{len(state.agent_tasks)}`\n"
                f"📚 KB: `{len(state.knowledge_base)}` docs\n"
                f"📖 Lessons: `{len(state.lesson_progress)}` langs"
    )

async def import_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("❌ Reply vao file JSON da xuat de nhap lai.", parse_mode=ParseMode.MARKDOWN)
        return
    doc = update.message.reply_to_message.document
    if not doc.file_name.endswith('.json'):
        await update.message.reply_text("❌ Chi chap nhan file JSON.", parse_mode=ParseMode.MARKDOWN)
        return
    status_msg = await update.message.reply_text("📥 Dang nhap du lieu...", parse_mode=ParseMode.MARKDOWN)
    file = await context.bot.get_file(doc.file_id)
    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session
    async with session.get(file.file_path) as resp:
        data = await resp.json()
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if "history" in data:
        state.history = data["history"]
    if "branches" in data:
        state.branches = {}
        for bid, bdata in data["branches"].items():
            branch = ConversationBranch(bid, None, bdata.get("name", "Unknown"))
            branch.messages = bdata.get("messages", [])
            state.branches[bid] = branch
    if "self_notes" in data:
        state.self_notes = data["self_notes"]
    if "snippet_storage" in data:
        state.snippet_storage = data["snippet_storage"]
    if "whiteboard" in data:
        state.whiteboard = data["whiteboard"]
    if "lesson_progress" in data:
        for lang, lp in data["lesson_progress"].items():
            state.lesson_progress[lang] = LessonProgress(**lp)
    _save_state()
    await status_msg.edit_text(
        f"✅ Da nhap du lieu!\n\n"
        f"💬 History: `{len(state.history)}` msgs\n"
        f"🌿 Branches: `{len(state.branches)}`\n"
        f"🧠 Notes: `{len(state.self_notes)}`",
        parse_mode=ParseMode.MARKDOWN
    )

async def branch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if not context.args:
        current = state.branches.get(state.current_branch_id)
        msg = (
            f"🌿 Conversation Branches\n"
            f"{'━' * 22}\n\n"
            f"🌳 Hien tai: `{state.current_branch_id}` — {current.name if current else 'Unknown'}\n"
            f"📊 Tong branches: `{len(state.branches)}`\n\n"
            f"📋 Lenh:\n"
            f"• /branch new <ten> — Tao nhanh moi\n"
            f"• /branch switch <id> — Chuyen nhanh\n"
            f"• /branch list — Liet ke\n"
            f"• /branch merge <id> — Gop vao nhanh hien tai\n"
            f"• /branch delete <id> — Xoa nhanh"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return
    subcmd = context.args[0].lower()
    if subcmd == "new":
        name = " ".join(context.args[1:]) if len(context.args) > 1 else f"Branch {len(state.branches)+1}"
        branch_id = generate_branch_id()
        new_branch = ConversationBranch(branch_id, state.current_branch_id, name)
        current = state.branches.get(state.current_branch_id)
        if current:
            new_branch.messages = current.messages.copy()
        state.branches[branch_id] = new_branch
        state.current_branch_id = branch_id
        _save_state()
        await update.message.reply_text(
            f"🌿 Nhanh Moi Da Tao!\n🆔 `{branch_id}`\n📛 `{name}`\n👤 Parent: `{new_branch.parent_id}`",
            parse_mode=ParseMode.MARKDOWN
        )
    elif subcmd == "switch" and len(context.args) > 1:
        branch_id = context.args[1]
        if branch_id in state.branches:
            state.current_branch_id = branch_id
            branch = state.branches[branch_id]
            state.history = branch.messages.copy()
            _save_state()
            await update.message.reply_text(
                f"🌿 Da chuyen nhanh!\n🆔 `{branch_id}`\n📛 `{branch.name}`\n💬 `{len(branch.messages)}` messages",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Khong tim thay nhanh.", parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "list":
        msg = f"🌿 Danh Sach Branches\n{'━' * 22}\n\n"
        for bid, branch in state.branches.items():
            prefix = "✅ " if bid == state.current_branch_id else "  "
            msg += f"{prefix}`{bid}` — {branch.name} ({len(branch.messages)} msgs)\n"
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "merge" and len(context.args) > 1:
        branch_id = context.args[1]
        if branch_id not in state.branches:
            await update.message.reply_text("❌ Khong tim thay nhanh.", parse_mode=ParseMode.MARKDOWN)
            return
        source = state.branches[branch_id]
        current = state.branches[state.current_branch_id]
        current.messages.extend(source.messages)
        state.history = current.messages.copy()
        _save_state()
        await update.message.reply_text(
            f"🔀 Da gop nhanh!\n📥 `{branch_id}` → `{state.current_branch_id}`\n💬 Tong: `{len(current.messages)}` messages",
            parse_mode=ParseMode.MARKDOWN
        )
    elif subcmd == "delete" and len(context.args) > 1:
        branch_id = context.args[1]
        if branch_id == "main":
            await update.message.reply_text("❌ Khong the xoa nhanh main.", parse_mode=ParseMode.MARKDOWN)
            return
        if branch_id in state.branches:
            del state.branches[branch_id]
            if state.current_branch_id == branch_id:
                state.current_branch_id = "main"
                state.history = state.branches["main"].messages.copy()
            _save_state()
            await update.message.reply_text(f"🗑 Da xoa nhanh: `{branch_id}`", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ Khong tim thay nhanh.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Lenh branch khong hop le.", parse_mode=ParseMode.MARKDOWN)

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "⏰ Hen Gio Nhac Nho\n"
            f"{'━' * 22}\n\n"
            "Cu phap: /remind <time> <message>\n\n"
            "Thoi gian:\n• 10s — 10 giay\n• 5m — 5 phut\n• 2h — 2 gio\n• 1d — 1 ngay\n\n"
            "Vi du:\n• /remind 10m uong nuoc\n• /remind 2h hop team",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    time_str = context.args[0].lower()
    message = " ".join(context.args[1:])
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r'(\d+)([smhd])', time_str)
    if not match:
        await update.message.reply_text("❌ Dinh dang thoi gian khong hop le.", parse_mode=ParseMode.MARKDOWN)
        return
    amount, unit = int(match.group(1)), match.group(2)
    seconds = amount * multiplier[unit]
    if seconds > 604800:
        await update.message.reply_text("❌ Toi da 7 ngay.", parse_mode=ParseMode.MARKDOWN)
        return
    trigger_time = datetime.now() + timedelta(seconds=seconds)
    job_id = generate_job_id()
    job = ScheduledJob(
        job_id=job_id, user_id=update.effective_user.id, description=message,
        trigger_time=trigger_time, command="remind", args=message
    )
    scheduled_jobs_global.append(job)
    await update.message.reply_text(
        f"⏰ Da dat nhac nho!\n\n📝 `{message}`\n⏱ Sau: `{amount}{unit}`\n🕐 Luc: `{trigger_time.strftime('%H:%M:%S')}`\n🆔 `{job_id}`",
        parse_mode=ParseMode.MARKDOWN
    )
    async def send_reminder():
        await asyncio.sleep(seconds)
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⏰ Nhac Nho!\n\n📝 `{message}`\n🕐 Da den gio!",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Reminder error: {e}")
    asyncio.create_task(send_reminder())

async def persona_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if not context.args:
        await update.message.reply_text(
            "🎭 Tinh Cach AI\n"
            f"{'━' * 20}\n\n"
            "Cu phap: /persona <mo ta>\n\n"
            "Vi du:\n• /persona Ban la senior dev Python, noi ngan gon\n"
            "• /persona Ban la giao vien tieng Anh, kien nhan",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    persona = " ".join(context.args)
    state.self_notes.append(f"Persona: {persona}")
    _save_state()
    await update.message.reply_text(
        f"🎭 Da dat tinh cach!\n\n📝 `{persona[:200]}`\n\n💡 AI se ap dung trong cac cuoc tro chuyen toi.",
        parse_mode=ParseMode.MARKDOWN
    )

async def whiteboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if not context.args:
        await update.message.reply_text(
            "📝 Whiteboard\n"
            f"{'━' * 20}\n\n"
            "• /whiteboard add <noi dung> — Them\n"
            "• /whiteboard clear — Xoa\n"
            "• /whiteboard show — Xem\n\n"
            f"Hien tai: `{len(state.whiteboard)}` ky tu",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    subcmd = context.args[0].lower()
    if subcmd == "add":
        content = " ".join(context.args[1:])
        state.whiteboard += f"\n[{datetime.now().strftime('%H:%M')}] {content}"
        _save_state()
        await update.message.reply_text("✅ Da them vao whiteboard!", parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "clear":
        state.whiteboard = ""
        _save_state()
        await update.message.reply_text("🗑 Da xoa whiteboard!", parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "show":
        if not state.whiteboard:
            await update.message.reply_text("📭 Whiteboard trong.", parse_mode=ParseMode.MARKDOWN)
            return
        await send_long_text(update, f"📝 Whiteboard\n{'━' * 20}\n\n{state.whiteboard}", filename="whiteboard.md", format_hint="md")
    else:
        await update.message.reply_text("❌ Lenh khong hop le.", parse_mode=ParseMode.MARKDOWN)

async def snippet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if not context.args:
        await update.message.reply_text(
            "📦 Code Snippets\n"
            f"{'━' * 20}\n\n"
            "• /snippet save <ten> — Luu (reply code)\n"
            "• /snippet list — Xem danh sach\n"
            "• /snippet get <ten> — Lay code\n"
            "• /snippet delete <ten> — Xoa\n\n"
            f"Hien tai: `{len(state.snippet_storage)}` snippets",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    subcmd = context.args[0].lower()
    if subcmd == "save" and len(context.args) > 1:
        name = context.args[1]
        code = ""
        if update.message.reply_to_message and update.message.reply_to_message.text:
            code = update.message.reply_to_message.text
        if not code:
            await update.message.reply_text("❌ Reply vao code de luu.", parse_mode=ParseMode.MARKDOWN)
            return
        state.snippet_storage[name] = code
        _save_state()
        await update.message.reply_text(f"✅ Da luu snippet: `{name}`", parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "list":
        if not state.snippet_storage:
            await update.message.reply_text("📭 Chua co snippet nao.", parse_mode=ParseMode.MARKDOWN)
            return
        msg = f"📦 Snippets\n{'━' * 20}\n\n"
        for name, code in state.snippet_storage.items():
            msg += f"• `{name}` — {len(code)} chars\n"
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "get" and len(context.args) > 1:
        name = context.args[1]
        if name in state.snippet_storage:
            code = state.snippet_storage[name]
            await send_long_text(update, f"📦 `{name}`\n{'━' * 20}\n\n```\n{code}\n```", filename=f"snippet_{name}.py")
        else:
            await update.message.reply_text("❌ Khong tim thay snippet.", parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "delete" and len(context.args) > 1:
        name = context.args[1]
        if name in state.snippet_storage:
            del state.snippet_storage[name]
            _save_state()
            await update.message.reply_text(f"🗑 Da xoa snippet: `{name}`", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ Khong tim thay snippet.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Lenh khong hop le.", parse_mode=ParseMode.MARKDOWN)

async def format_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        code = update.message.reply_to_message.text
    elif context.args:
        code = " ".join(context.args)
    if not code:
        await update.message.reply_text("❌ Reply code hoac go: /format <code>", parse_mode=ParseMode.MARKDOWN)
        return
    status_msg = await update.message.reply_text("🎨 Dang format code...", parse_mode=ParseMode.MARKDOWN)
    success, formatted, error = await CodeFormatter.format_python(code)
    if success:
        await status_msg.edit_text(
            f"✅ Format thanh cong!\n\n```python\n{formatted[:3500]}\n```",
            parse_mode=ParseMode.MARKDOWN
        )
        if len(formatted) > 3500:
            await send_long_text(update, formatted, filename="formatted.py")
    else:
        await status_msg.edit_text(f"❌ Format that bai:\n`{error[:500]}`", parse_mode=ParseMode.MARKDOWN)

async def kb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if not context.args:
        await update.message.reply_text(
            "📚 Knowledge Base (RAG)\n"
            f"{'━' * 22}\n\n"
            "• /kb upload — Upload file (reply vao file)\n"
            "• /kb ask <cau hoi> — Hoi dua tren tai lieu\n"
            "• /kb list — Xem tai lieu da upload\n"
            "• /kb clear — Xoa toan bo KB\n\n"
            f"Hien tai: `{len(state.knowledge_base)}` documents",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    subcmd = context.args[0].lower()
    if subcmd == "upload":
        if not update.message.reply_to_message or not update.message.reply_to_message.document:
            await update.message.reply_text("❌ Reply vao tin nhan co file (PDF, TXT, DOCX) de upload.", parse_mode=ParseMode.MARKDOWN)
            return
        doc = update.message.reply_to_message.document
        if doc.file_size > 5 * 1024 * 1024:
            await update.message.reply_text("❌ File qua lon (>5MB).", parse_mode=ParseMode.MARKDOWN)
            return
        status_msg = await update.message.reply_text("📤 Dang tai file...", parse_mode=ParseMode.MARKDOWN)
        file = await context.bot.get_file(doc.file_id)
        session = context.bot_data.get('session')
        if not session:
            session = aiohttp.ClientSession()
            context.bot_data['session'] = session
        async with session.get(file.file_path) as resp:
            file_bytes = await resp.read()
        try:
            text = file_bytes.decode('utf-8', errors='ignore')
        except:
            text = str(file_bytes)
        chunks = SimpleRAG.chunk_text(text, chunk_size=1000, overlap=100)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
        payload = {"model": "text-embedding-3-small", "input": text[:4000]}
        async with session.post(API_EMBED_URL, headers=headers, json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                embedding = result.get('data', [{}])[0].get('embedding', [])
            else:
                embedding = []
        doc_id = generate_doc_id()
        knowledge_doc = KnowledgeDocument(
            doc_id=doc_id, filename=doc.file_name, content=text,
            embedding=embedding, chunk_count=len(chunks)
        )
        state.knowledge_base.append(knowledge_doc)
        state.stats.files_processed += 1
        _save_state()
        await status_msg.edit_text(
            f"✅ Da upload!\n\n📄 `{doc.file_name}`\n🆔 `{doc_id}`\n📊 Size: `{len(text)}` chars\n🧩 Chunks: `{len(chunks)}`\n📚 Tong KB: `{len(state.knowledge_base)}` docs",
            parse_mode=ParseMode.MARKDOWN
        )
    elif subcmd == "ask":
        if len(context.args) < 2:
            await update.message.reply_text("❌ Cu phap: /kb ask <cau hoi>", parse_mode=ParseMode.MARKDOWN)
            return
        query = " ".join(context.args[1:])
        if not state.knowledge_base:
            await update.message.reply_text("📭 KB trong. Upload tai lieu truoc bang /kb upload.", parse_mode=ParseMode.MARKDOWN)
            return
        status_msg = await update.message.reply_text("🧠 Dang truy van KB...", parse_mode=ParseMode.MARKDOWN)
        session = context.bot_data.get('session')
        if not session:
            session = aiohttp.ClientSession()
            context.bot_data['session'] = session
        results = await SimpleRAG.query_knowledge_base(session, query, state.knowledge_base)
        if not results:
            await status_msg.edit_text("❌ Khong tim thay thong tin lien quan.", parse_mode=ParseMode.MARKDOWN)
            return
        context_text = "\n\n".join([f"[Tu {fname} — do tuong dong {score:.2f}]:\n{content[:500]}" for fname, score, content in results])
        messages = [
            {"role": "system", "content": "Tra loi cau hoi dua tren tai lieu duoc cung cap. Neu khong co thong tin, hay noi ro."},
            {"role": "user", "content": f"Cau hoi: {query}\n\nTai lieu tham khao:\n{context_text}"}
        ]
        answer, metrics = await call_chat_api(session, DEFAULT_CHAT_MODEL, messages, status_msg, max_tokens=2048)
        sources = "\n".join([f"• `{fname}` ({score:.2f})" for fname, score, _ in results])
        await status_msg.edit_text(
            f"📚 Tra Loi Tu KB\n"
            f"{'━' * 22}\n\n"
            f"❓ Cau hoi: `{query}`\n\n"
            f"💡 Tra loi:\n{answer}\n\n"
            f"📎 Nguon:\n{sources}",
            parse_mode=ParseMode.MARKDOWN
        )
    elif subcmd == "list":
        if not state.knowledge_base:
            await update.message.reply_text("📭 KB trong.", parse_mode=ParseMode.MARKDOWN)
            return
        msg = f"📚 Knowledge Base Documents\n{'━' * 24}\n\n"
        for i, doc in enumerate(state.knowledge_base, 1):
            msg += f"{i}. 📄 `{doc.filename}`\n   🆔 `{doc.doc_id}` | 🧩 `{doc.chunk_count}` chunks\n"
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "clear":
        count = len(state.knowledge_base)
        state.knowledge_base = []
        _save_state()
        await update.message.reply_text(f"🗑 Da xoa {count} tai lieu.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Lenh KB khong hop le.", parse_mode=ParseMode.MARKDOWN)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Cu phap: /search <query>\nVi du: /search Python asyncio best practices", parse_mode=ParseMode.MARKDOWN)
        return
    query = " ".join(context.args)
    status_msg = await update.message.reply_text(f"🔍 Dang tim: `{query}`...", parse_mode=ParseMode.MARKDOWN)
    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session
    results = await web_search(session, query, 5)
    msg = f"🔍 Ket Qua Tim Kiem\n{'━' * 22}\n\n"
    for i, r in enumerate(results, 1):
        msg += f"{i}. *{r['title']}*\n   🔗 {r['url']}\n   📝 {r['snippet'][:100]}...\n\n"
    await status_msg.edit_text(msg, parse_mode=ParseMode.MARKDOWN)

async def fetch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Cu phap: /fetch <url>", parse_mode=ParseMode.MARKDOWN)
        return
    url = context.args[0]
    status_msg = await update.message.reply_text(f"🌐 Dang tai: `{url}`...", parse_mode=ParseMode.MARKDOWN)
    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session
    content = await fetch_webpage(session, url)
    await status_msg.delete()
    await send_long_text(update, f"🌐 Noi Dung Trang Web\n{'━' * 22}\n\n{content}", filename="webpage.txt")

async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    code = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        code = update.message.reply_to_message.text
    elif context.args:
        code = " ".join(context.args)
    if not code:
        await update.message.reply_text(
            "❌ Cung cap code Python de chay:\n"
            "• Reply vao tin nhan chua code va go /run\n"
            "• Hoac: /run print('hello')\n\n"
            "⚠️ Han che: Khong cho phep file I/O, network, system calls.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    status_msg = await update.message.reply_text("🐍 Dang chay code...", parse_mode=ParseMode.MARKDOWN)
    success, stdout, stderr = await CodeInterpreter.execute(code, timeout=30)
    state.stats.code_executed += 1
    _save_state()
    result_emoji = "✅" if success else "❌"
    output = stdout if stdout else "(khong co output)"
    error = stderr if stderr else ""
    report = (
        f"{result_emoji} Ket Qua Thuc Thi\n"
        f"{'━' * 24}\n\n"
        f"📤 Output:\n```\n{truncate_text(output, 3500)}\n```\n"
    )
    if error:
        report += f"📛 Error:\n```\n{truncate_text(error, 1500)}\n```\n"
    await status_msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)

async def runplot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    code = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        code = update.message.reply_to_message.text
    elif context.args:
        code = " ".join(context.args)
    if not code:
        await update.message.reply_text(
            "❌ Cung cap code Python co Matplotlib:\n"
            "• Reply vao code va go /runplot\n"
            "• Vi du: /runplot import matplotlib.pyplot as plt; plt.plot([1,2,3]); plt.title('Test')",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    status_msg = await update.message.reply_text("📊 Dang chay code + ve do thi...", parse_mode=ParseMode.MARKDOWN)
    success, stdout, stderr, img_bytes = await CodeInterpreter.execute_with_matplotlib(code, timeout=30)
    state.stats.code_executed += 1
    _save_state()
    output = stdout if stdout else "(khong co output)"
    error = stderr if stderr else ""
    report = (
        f"{'✅' if success else '❌'} Ket Qua Thuc Thi + Matplotlib\n"
        f"{'━' * 24}\n\n"
        f"📤 Output:\n```\n{truncate_text(output, 2000)}\n```\n"
    )
    if error:
        report += f"📛 Error:\n```\n{truncate_text(error, 1000)}\n```\n"
    await status_msg.delete()
    if img_bytes:
        bio = io.BytesIO(img_bytes)
        bio.name = f"plot_{int(time.time())}.png"
        await update.message.reply_photo(photo=bio, caption=report[:1024], parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(report, parse_mode=ParseMode.MARKDOWN)

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        code = update.message.reply_to_message.text
    elif context.args:
        code = " ".join(context.args)
    if not code:
        await update.message.reply_text(
            "❌ Cung cap code de phan tich:\n"
            "• Reply vao tin nhan chua code va go /analyze\n"
            "• Hoac: /analyze <code>",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    status_msg = await update.message.reply_text("🔍 Dang phan tich code...", parse_mode=ParseMode.MARKDOWN)
    result = await agent_analyze_code(code)
    score_bar = build_progress_bar(result["score"], 100, 15)
    report = (
        f"🔍 Ket Qua Phan Tich Code\n"
        f"{'━' * 24}\n\n"
        f"📊 Quality Score: `{result['score']}/100`\n"
        f"`{score_bar}`\n"
        f"📄 Ngon ngu: `{result['language']}` | Dong: `{result['lines']}`\n\n"
    )
    if result["issues"]:
        report += f"❌ Loi Nghiem Trong ({len(result['issues'])}):\n"
        for issue in result["issues"]:
            report += f"  • {issue}\n"
        report += "\n"
    if result["warnings"]:
        report += f"⚠️ Canh Bao ({len(result['warnings'])}):\n"
        for warning in result["warnings"]:
            report += f"  • {warning}\n"
        report += "\n"
    if result["info"]:
        report += f"✅ Thong Tin ({len(result['info'])}):\n"
        for info in result["info"]:
            report += f"  • {info}\n"
    if not result["issues"] and not result["warnings"]:
        report += "🎉 Code sach! Khong phat hien van de.\n"
    await status_msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)

async def docker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_type = context.args[0] if context.args else "python"
    dockerfile = generate_dockerfile(project_type)
    bio = io.BytesIO(dockerfile.encode('utf-8'))
    bio.name = "Dockerfile"
    await update.message.reply_document(
        document=bio,
        caption=f"🐳 Dockerfile cho {project_type}\n\n💡 Dung /git push owner/repo Dockerfile de push len GitHub.",
        parse_mode=ParseMode.MARKDOWN
    )

async def cicd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_type = context.args[0] if context.args else "python"
    workflow = generate_github_actions(project_type)
    bio = io.BytesIO(workflow.encode('utf-8'))
    bio.name = "ci.yml"
    await update.message.reply_document(
        document=bio,
        caption=f"⚙️ GitHub Actions cho {project_type}\n\n💡 Dung /git workflow owner/repo ci de push.",
        parse_mode=ParseMode.MARKDOWN
    )

async def diff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args and not (update.message.reply_to_message and update.message.reply_to_message.text):
        await update.message.reply_text("❌ Cu phap: /diff <code1> | <code2>\nHoac reply vao code1, go /diff <code2>", parse_mode=ParseMode.MARKDOWN)
        return
    text = " ".join(context.args) if context.args else ""
    if "|" in text:
        parts = text.split("|", 1)
        code1, code2 = parts[0].strip(), parts[1].strip()
    elif update.message.reply_to_message:
        code1 = update.message.reply_to_message.text
        code2 = text
    else:
        await update.message.reply_text("❌ Can 2 doan code de so sanh.", parse_mode=ParseMode.MARKDOWN)
        return
    diff_text = CodeFormatter.format_diff(code1, code2)
    if not diff_text.strip():
        await update.message.reply_text("✅ Hai doan code giong nhau!", parse_mode=ParseMode.MARKDOWN)
        return
    await update.message.reply_text(
        f"🔍 Diff Result\n"
        f"{'━' * 20}\n"
        f"```\n{diff_text}\n```",
        parse_mode=ParseMode.MARKDOWN
    )

async def testgen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        code = update.message.reply_to_message.text
    elif context.args:
        code = " ".join(context.args)
    if not code:
        await update.message.reply_text("❌ Reply code hoac go: /testgen <code>", parse_mode=ParseMode.MARKDOWN)
        return
    status_msg = await update.message.reply_text("🧪 Dang tao unit tests...", parse_mode=ParseMode.MARKDOWN)
    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session
    prompt = (
        f"Viet unit tests day du cho code sau bang pytest:\n\n"
        f"```python\n{code}\n```\n\n"
        f"Yeu cau:\n"
        f"- Bao phu cac truong hop chinh, edge cases, loi\n"
        f"- Dung pytest va fixtures neu can\n"
        f"- Bao gom docstring giai thich moi test\n"
        f"- Chi tra ve code test, khong giai thich"
    )
    messages = [{"role": "user", "content": prompt}]
    test_code, metrics = await call_chat_api(session, "claude-sonnet-4.6", messages, status_msg, max_tokens=4096)
    await status_msg.delete()
    await send_long_text(update, f"🧪 Unit Tests Generated\n{'━' * 20}\n\n```python\n{test_code}\n```", filename="test_generated.py")

async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Cu phap: /image <mo ta>\n"
            "Vi du: /image a futuristic city at sunset, cyberpunk style",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    prompt = " ".join(context.args)
    status_msg = await update.message.reply_text("🎨 Dang tao hinh anh...", parse_mode=ParseMode.MARKDOWN)
    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session
    try:
        image_bytes, info = await call_image_api(session, prompt, status_msg=status_msg)
        bio = io.BytesIO(image_bytes)
        bio.name = f"generated_{int(time.time())}.png"
        await status_msg.delete()
        await update.message.reply_photo(
            photo=bio,
            caption=f"🎨 Generated Image\n\n📝 Prompt: `{prompt[:100]}`\nℹ️ {info}"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Loi tao anh: `{str(e)[:300]}`", parse_mode=ParseMode.MARKDOWN)

async def tts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args and not (update.message.reply_to_message and update.message.reply_to_message.text):
        await update.message.reply_text("❌ Cu phap: /tts <van ban>\nHoac reply vao tin nhan van ban.", parse_mode=ParseMode.MARKDOWN)
        return
    text = " ".join(context.args) if context.args else update.message.reply_to_message.text
    status_msg = await update.message.reply_text("🔊 Dang tong hop giong noi...", parse_mode=ParseMode.MARKDOWN)
    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session
    try:
        audio_bytes, metrics = await call_tts_api(session, DEFAULT_TTS_MODEL, text, status_msg)
        bio = io.BytesIO(audio_bytes)
        bio.name = f"tts_{int(time.time())}.mp3"
        await status_msg.delete()
        await update.message.reply_voice(
            voice=bio,
            caption=f"🔊 Text-to-Speech\n📝 `{len(text)}` chars | 📦 `{len(audio_bytes)}` bytes"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Loi TTS: `{str(e)[:300]}`", parse_mode=ParseMode.MARKDOWN)

async def stt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.voice:
        await update.message.reply_text(
            "❌ Reply vao tin nhan voice message de chuyen thanh text.\n"
            "(Tinh nang nay can integration voi Whisper API)",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    await update.message.reply_text(
        "🎤 Speech-to-Text\n"
        "Dang tai file voice... (can tich hop Whisper API day du)\n"
        "Tam thoi: Hay dung /tts de tao giong noi tu text.",
        parse_mode=ParseMode.MARKDOWN
    )

async def vision_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(
            "❌ Reply vao tin nhan anh de phan tich.\n"
            "Vi du: Gui anh → Reply anh → Go /vision",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    status_msg = await update.message.reply_text("👁 Dang phan tich hinh anh...", parse_mode=ParseMode.MARKDOWN)
    photo = update.message.reply_to_message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session
    async with session.get(file.file_path) as resp:
        image_bytes = await resp.read()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    prompt = " ".join(context.args) if context.args else "Describe this image in detail."
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }
    ]
    try:
        result, metrics = await call_chat_api(session, DEFAULT_VISION_MODEL, messages, status_msg, max_tokens=2048)
        await status_msg.delete()
        await update.message.reply_text(f"👁 Vision Analysis\n{'━' * 20}\n\n{result}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ Vision API Error: `{str(e)[:300]}`\n"
            f"Co the model khong ho tro vision. Thu doi model bang /models.",
            parse_mode=ParseMode.MARKDOWN
        )

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if not state.self_notes:
        await update.message.reply_text(
            "🧠 Chua co ghi chu tu hoc.\n"
            "AI se tu dong ghi nhan sau moi task.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    msg = f"🧠 Ghi Chu Tu Hoc Cua AI\n{'━' * 24}\n\n"
    for i, note in enumerate(state.self_notes[-20:], 1):
        msg += f"{i}. `{note[:120]}`\n"
    await send_long_text(update, msg, filename="self_notes.txt")

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if not state.agent_tasks:
        await update.message.reply_text(
            "📭 Chua co agent task nao.\n\nDung /agent <mo ta> de bat dau.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    msg = f"🤖 Lich Su Agent Tasks\n{'━' * 24}\n\n"
    for i, task in enumerate(state.agent_tasks[-10:], 1):
        status_emoji = {"completed": "✅", "failed": "❌", "running": "🔄",
                        "pending": "⏳", "planning": "📋", "coding": "💻",
                        "reviewing": "🔍", "testing": "🧪", "pushing": "🚀"}.get(task.status, "❓")
        msg += (
            f"{i}. {status_emoji} `{task.task_id}`\n"
            f"   📝 {task.description[:40]}...\n"
            f"   🤖 Model: {task.selected_model}\n"
            f"   💰 {format_vnd(task.cost_vnd)} VND | ⏰ {task.created_at}\n\n"
        )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# ============================ LESSON SYSTEM ============================

async def lesson_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)

    if not context.args:
        lang = state.preferences.learning_language
        lp = state.lesson_progress.get(lang)
        if not lp:
            lp = LessonProgress(lang)
            state.lesson_progress[lang] = lp

        # Get topics for this language
        topics = THEORY_TOPICS.get(lang, DEFAULT_TOPICS)
        current_lesson_num = lp.current_lesson

        if current_lesson_num >= len(topics):
            await update.message.reply_text(
                f"🎉 Chuc mung! Ban da hoan thanh tat ca {len(topics)} bai ly thuyet cua {LANGUAGE_DISPLAY.get(lang, lang)}!\n"
                f"Dung /leetcode de luyen tap hoac /lesson_lang de chon ngon ngu khac.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        topic = topics[current_lesson_num]
        status_msg = await update.message.reply_text(
            f"📚 Dang tao bai hoc {current_lesson_num + 1}/{len(topics)}: *{topic}*...\n"
            f"🤖 Model: `{DEFAULT_LESSON_MODEL}`\n"
            f"⏳ Vui long cho...",
            parse_mode=ParseMode.MARKDOWN
        )

        session = context.bot_data.get('session')
        if not session:
            session = aiohttp.ClientSession()
            context.bot_data['session'] = session

        # Build lesson prompt
        prev_topics = topics[max(0, current_lesson_num - 3):current_lesson_num]
        prev_summary = "; ".join(prev_topics) if prev_topics else "None"

        prompt = (
            f"Day la bai hoc so {current_lesson_num + 1} trong khoa hoc {LANGUAGE_DISPLAY.get(lang, lang)}.\n"
            f"Chu de: {topic}\n"
            f"Trinh do: {state.preferences.learning_level}\n"
            f"Cac bai truoc: {prev_summary}\n\n"
            f"Hay tao mot bai hoc hoan chinh theo dung 9 phan sau:\n"
            f"===SECTION 1: NHẮC LẠI BÀI CŨ===\n"
            f"===SECTION 2: NỘI DUNG BÀI MỚI===\n"
            f"===SECTION 3: CẤU TRÚC BÀI MỚI===\n"
            f"===SECTION 4: GIẢI THÍCH THUẬT NGỮ===\n"
            f"===SECTION 5: CODE CHỦ ĐẠO===\n"
            f"===SECTION 6: GIẢI THÍCH CODE===\n"
            f"===SECTION 7: CHỐT LẠI===\n"
            f"===SECTION 8: 3 CÂU HỎI===\n"
            f"===SECTION 9: LEETCODE MINI===\n\n"
            f"Su dung tieng Viet cho giai thich, tieng Anh cho code va thuat ngu ky thuat."
        )

        messages = [{"role": "user", "content": prompt}]
        try:
            lesson_text, metrics = await call_chat_api(
                session, DEFAULT_LESSON_MODEL, messages, status_msg,
                system_prompt=LESSON_SYSTEM_PROMPT, max_tokens=MAX_OUTPUT_TOKENS, temperature=0.7
            )

            lp.current_lesson = current_lesson_num + 1
            lp.completed_lessons.append(current_lesson_num)
            lp.last_studied = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            state.stats.lessons_completed += 1
            _save_state()

            await status_msg.delete()

            header = (
                f"📚 Bai Hoc {current_lesson_num + 1}/{len(topics)} — {LANGUAGE_DISPLAY.get(lang, lang)}\n"
                f"{'━' * 24}\n\n"
                f"📌 Chu de: *{topic}*\n"
                f"🎚 Trinh do: `{state.preferences.learning_level}`\n\n"
            )
            full_text = header + lesson_text

            await send_long_text(update, full_text, filename=f"lesson_{lang}_{current_lesson_num+1}.md", format_hint="md")

            # Send navigation buttons
            keyboard = [
                [InlineKeyboardButton("⏭ Bai tiep theo", callback_data="lesson_next")],
                [InlineKeyboardButton("🏆 LeetCode Mini", callback_data="lesson_leetcode")],
            ]
            await update.message.reply_text(
                "👆 Chon hanh dong tiep theo:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await status_msg.edit_text(f"❌ Loi tao bai hoc: `{str(e)[:300]}`", parse_mode=ParseMode.MARKDOWN)
        return

    subcmd = context.args[0].lower()
    if subcmd == "lang" and len(context.args) > 1:
        lang = context.args[1].lower()
        if lang in LEARNING_LANGUAGES:
            state.preferences.learning_language = lang
            if lang not in state.lesson_progress:
                state.lesson_progress[lang] = LessonProgress(lang)
            _save_state()
            await update.message.reply_text(
                f"✅ Da chon ngon ngu hoc: *{LANGUAGE_DISPLAY.get(lang, lang)}*\n"
                f"📚 Dung /lesson de bat dau hoc.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            langs_text = "\n".join([f"• `{l}` — {LANGUAGE_DISPLAY.get(l, l)}" for l in LEARNING_LANGUAGES[:10]])
            await update.message.reply_text(
                f"❌ Ngon ngu khong ho tro.\n\nCac ngon ngu ho tro:\n{langs_text}\n... va {len(LEARNING_LANGUAGES) - 10} ngon ngu khac.",
                parse_mode=ParseMode.MARKDOWN
            )
    elif subcmd == "next":
        await lesson_command(update, context)
    elif subcmd == "progress":
        lang = state.preferences.learning_language
        lp = state.lesson_progress.get(lang)
        if not lp:
            await update.message.reply_text("📭 Chua co tien do hoc tap.", parse_mode=ParseMode.MARKDOWN)
            return
        topics = THEORY_TOPICS.get(lang, DEFAULT_TOPICS)
        progress_bar = build_progress_bar(lp.current_lesson, len(topics), 20)
        await update.message.reply_text(
            f"📊 Tien Do Hoc Tap — {LANGUAGE_DISPLAY.get(lang, lang)}\n"
            f"{'━' * 24}\n\n"
            f"📖 Bai hien tai: `{lp.current_lesson + 1}/{len(topics)}`\n"
            f"`{progress_bar}`\n"
            f"✅ Da hoan thanh: `{len(lp.completed_lessons)}` bai\n"
            f"🏆 LeetCode giai: `{len(lp.leetcode_solved)}`\n"
            f"📝 Quiz scores: `{len(lp.quiz_scores)}`\n"
            f"🕐 Hoc gan nhat: `{lp.last_studied}`",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "📚 Lesson Commands:\n"
            "• /lesson — Bat dau bai hoc tiep theo\n"
            "• /lesson lang <ngon ngu> — Chon ngon ngu\n"
            "• /lesson next — Bai tiep theo\n"
            "• /lesson progress — Xem tien do",
            parse_mode=ParseMode.MARKDOWN
        )

async def lesson_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "lesson_next":
        await query.edit_message_text("⏭ Chuyen sang bai tiep theo...")
        # Simulate /lesson command
        update.message = query.message
        await lesson_command(update, context)
    elif data == "lesson_leetcode":
        await query.edit_message_text("🏆 Chuyen sang LeetCode Mini...")
        update.message = query.message
        await leetcode_command(update, context)

async def leetcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)

    if not context.args:
        # Show LeetCode menu
        keyboard = []
        for topic in LEETCODE_TOPICS[:8]:
            keyboard.append([InlineKeyboardButton(f"📌 {topic}", callback_data=f"leetcode_topic_{topic}")])
        keyboard.append([
            InlineKeyboardButton("🟢 Easy", callback_data="leetcode_diff_Easy"),
            InlineKeyboardButton("🟡 Medium", callback_data="leetcode_diff_Medium"),
            InlineKeyboardButton("🔴 Hard", callback_data="leetcode_diff_Hard"),
        ])
        await update.message.reply_text(
            f"🏆 LeetCode Practice\n"
            f"{'━' * 20}\n\n"
            f"📚 Chon chu de hoac do kho de bat dau:\n"
            f"📊 Da giai: `{state.stats.leetcode_solved}` bai",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    subcmd = context.args[0].lower()
    if subcmd == "topic" and len(context.args) > 1:
        topic = " ".join(context.args[1:])
        await _generate_leetcode(update, context, state, topic=topic)
    elif subcmd == "diff" and len(context.args) > 1:
        diff = context.args[1].capitalize()
        if diff in LEETCODE_DIFFICULTIES:
            await _generate_leetcode(update, context, state, difficulty=diff)
        else:
            await update.message.reply_text("❌ Do kho: Easy, Medium, Hard", parse_mode=ParseMode.MARKDOWN)
    elif subcmd == "random":
        await _generate_leetcode(update, context, state)
    else:
        await update.message.reply_text(
            "🏆 LeetCode Commands:\n"
            "• /leetcode — Menu chinh\n"
            "• /leetcode topic <chu de> — Chon chu de\n"
            "• /leetcode diff <easy/medium/hard> — Chon do kho\n"
            "• /leetcode random — Bai ngau nhien",
            parse_mode=ParseMode.MARKDOWN
        )

async def leetcode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    state = await get_user_state(user_id)

    if data.startswith("leetcode_topic_"):
        topic = data.replace("leetcode_topic_", "")
        await query.edit_message_text(f"📌 Dang tao bai {topic}...")
        update.message = query.message
        await _generate_leetcode(update, context, state, topic=topic)
    elif data.startswith("leetcode_diff_"):
        diff = data.replace("leetcode_diff_", "")
        await query.edit_message_text(f"🎯 Dang tao bai {diff}...")
        update.message = query.message
        await _generate_leetcode(update, context, state, difficulty=diff)

async def _generate_leetcode(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState, 
                              topic: str = None, difficulty: str = None):
    lang = state.preferences.learning_language

    # Select random topic/difficulty if not specified
    if not topic:
        topic = random.choice(LEETCODE_TOPICS)
    if not difficulty:
        difficulty = random.choice(LEETCODE_DIFFICULTIES)

    status_msg = await update.message.reply_text(
        f"🏆 Dang tao bai LeetCode...\n"
        f"📌 Chu de: `{topic}`\n"
        f"🎯 Do kho: `{difficulty}`\n"
        f"💻 Ngon ngu: `{LANGUAGE_DISPLAY.get(lang, lang)}`",
        parse_mode=ParseMode.MARKDOWN
    )

    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session

    prompt = (
        f"Tao mot bai tap LeetCode-style ve chu de '{topic}' voi do kho '{difficulty}'.\n"
        f"Ngon ngu lap trinh: {lang}\n\n"
        f"Yeu cau:\n"
        f"1. De bai ro rang, co vi du input/output\n"
        f"2. Giai thich thuat toan\n"
        f"3. Code giai phap toi uu\n"
        f"4. Phan tich do phuc tap thoi gian/khong gian\n"
        f"5. 2-3 goi y (khong tiet lo dap an)\n"
        f"6. Test cases\n\n"
        f"Format: Su dung tieng Viet cho giai thich, tieng Anh cho code."
    )

    messages = [{"role": "user", "content": prompt}]
    try:
        problem_text, metrics = await call_chat_api(
            session, DEFAULT_LESSON_MODEL, messages, status_msg,
            max_tokens=MAX_OUTPUT_TOKENS, temperature=0.7
        )

        state.stats.leetcode_solved += 1
        lp = state.lesson_progress.get(lang)
        if lp:
            lp.leetcode_solved.append(int(time.time()))
        _save_state()

        await status_msg.delete()

        header = (
            f"🏆 LeetCode — {topic}\n"
            f"{'━' * 20}\n\n"
            f"🎯 Do kho: `{difficulty}`\n"
            f"💻 Ngon ngu: `{LANGUAGE_DISPLAY.get(lang, lang)}`\n\n"
        )
        await send_long_text(update, header + problem_text, filename=f"leetcode_{topic.replace(' ', '_')}.md", format_hint="md")

    except Exception as e:
        await status_msg.edit_text(f"❌ Loi tao bai LeetCode: `{str(e)[:300]}`", parse_mode=ParseMode.MARKDOWN)

async def lesson_lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        langs_text = "\n".join([f"• `{l}` — {LANGUAGE_DISPLAY.get(l, l)}" for l in LEARNING_LANGUAGES])
        await update.message.reply_text(
            f"📚 Chon Ngon Ngu Hoc\n"
            f"{'━' * 20}\n\n"
            f"Cu phap: /lesson_lang <ngon ngu>\n\n"
            f"Cac ngon ngu ho tro:\n{langs_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    lang = context.args[0].lower()
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    if lang in LEARNING_LANGUAGES:
        state.preferences.learning_language = lang
        if lang not in state.lesson_progress:
            state.lesson_progress[lang] = LessonProgress(lang)
        _save_state()
        await update.message.reply_text(
            f"✅ Da chon ngon ngu hoc: *{LANGUAGE_DISPLAY.get(lang, lang)}*\n"
            f"📚 Dung /lesson de bat dau hoc.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("❌ Ngon ngu khong ho tro. Dung /lesson_lang de xem danh sach.", parse_mode=ParseMode.MARKDOWN)

# ============================ GITHUB COMMANDS ============================

async def git_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            f"🌐 GitHub Agent — Full Control\n"
            f"{'━' * 26}\n\n"
            f"📦 Repository:\n"
            f"• /git repo <ten> [desc] [private] — Tao repo\n"
            f"• /git get <o/r> <path> — Doc file\n"
            f"• /git list <o/r> [path] — Liet ke\n"
            f"• /git commits <o/r> — Xem commits\n"
            f"• /git search <query> — Tim repo\n"
            f"• /git fork <o/r> — Fork repo\n"
            f"• /git star <o/r> — Star repo\n"
            f"• /git rate — Xem rate limit\n\n"
            f"📝 File Operations:\n"
            f"• /git push <o/r> <path> — Push (reply code)\n"
            f"• /git update <o/r> <path> — Update (reply code)\n"
            f"• /git delete <o/r> <path> — Xoa\n\n"
            f"🌿 Branch & PR:\n"
            f"• /git branch <o/r> <new> — Tao branch\n"
            f"• /git pr <o/r> <title> <head> <base> — Tao PR\n"
            f"• /git issue <o/r> <title> — Tao issue\n"
            f"• /git release <o/r> <tag> [name] — Tao release\n"
            f"• /git workflow <o/r> <name> — Tao CI workflow\n\n"
            f"💡 Meo: Dung reply de push code dai",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    subcmd = context.args[0].lower()
    handlers = {
        "repo": _git_repo, "push": _git_push, "get": _git_get,
        "list": _git_list, "branch": _git_branch, "pr": _git_pr,
        "delete": _git_delete, "commits": _git_commits, "update": _git_update,
        "issue": _git_issue, "release": _git_release, "workflow": _git_workflow,
        "search": _git_search, "fork": _git_fork, "star": _git_star,
        "rate": _git_rate,
    }
    if subcmd in handlers:
        await handlers[subcmd](update, context)
    else:
        await update.message.reply_text(
            f"❌ Lenh GitHub khong hop le: `{subcmd}`\nDung /git de xem danh sach.",
            parse_mode=ParseMode.MARKDOWN
        )

async def _git_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Cu phap: /git repo <ten> [description] [private]\nVi du: /git repo my-project Bot AI cua toi",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    repo_name = sanitize_repo_name(context.args[1])
    description = " ".join(context.args[2:]) if len(context.args) > 2 else ""
    private = "private" in description.lower()
    if private:
        description = description.replace("private", "").strip()
    status_msg = await update.message.reply_text(f"⏳ Dang tao repository...\n📦 `{repo_name}`", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.create_repo(repo_name, description, private)
        if success:
            repo_url = data.get("html_url", "")
            clone_url = data.get("clone_url", "")
            await status_msg.edit_text(
                f"✅ Repository da tao!\n\n📦 Ten: `{repo_name}`\n🔗 URL: {repo_url}\n📥 Clone: `{clone_url}`\n🔒 Private: `{'Co' if private else 'Khong'}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi tao repo:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_push(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Cu phap: /git push <owner/repo> <path>\nReply vao tin nhan chua code.", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    file_path = context.args[2]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    content = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        content = update.message.reply_to_message.text
    elif len(context.args) > 3:
        content = " ".join(context.args[3:])
    if not content:
        await update.message.reply_text("❌ Thieu noi dung file!", parse_mode=ParseMode.MARKDOWN)
        return
    status_msg = await update.message.reply_text(f"⏳ Dang push file...\n📁 `{file_path}` → `{repo_path}`", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.create_file(owner, repo, file_path, content, f"feat: add {file_path} via Denia Bot")
        if success:
            file_url = data.get("content", {}).get("html_url", "") if isinstance(data, dict) else ""
            await status_msg.edit_text(
                f"✅ Da push file!\n\n📁 File: `{file_path}`\n📦 Repo: `{repo_path}`\n🔗 URL: {file_url}\n📊 Size: `{len(content)}` chars",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi push:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Cu phap: /git get <owner/repo> <path>", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    file_path = context.args[2]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text(f"⏳ Dang lay file...\n📁 `{file_path}` from `{repo_path}`", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.get_file(owner, repo, file_path)
        if success:
            content_encoded = data.get("content", "") if isinstance(data, dict) else ""
            try:
                content = base64.b64decode(content_encoded.replace("\n", "")).decode('utf-8')
            except:
                content = content_encoded
            size = data.get("size", len(content)) if isinstance(data, dict) else len(content)
            sha = data.get("sha", "")[:8] if isinstance(data, dict) else ""
            header = (
                f"📄 File Content\n"
                f"{'━' * 20}\n"
                f"📁 Path: `{file_path}`\n"
                f"📦 Repo: `{repo_path}`\n"
                f"📊 Size: `{size}` bytes\n"
                f"🔑 SHA: `{sha}...`\n\n"
            )
            full_text = header + f"```\n{content}\n```"
            await status_msg.delete()
            await send_long_text(update, full_text, filename=file_path.replace("/", "_"))
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Cu phap: /git list <owner/repo> [path]", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    path = context.args[2] if len(context.args) > 2 else ""
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text("⏳ Dang liet ke files...", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.list_files(owner, repo, path)
        if success and isinstance(data, list):
            msg = f"📂 File List — `{repo_path}`\n{'━' * 22}\n\n"
            for item in data:
                item_type = item.get("type", "")
                name = item.get("name", "")
                size = item.get("size", 0)
                emoji = "📁" if item_type == "dir" else "📄"
                msg += f"{emoji} `{name}`"
                if item_type == "file":
                    msg += f" ({size} bytes)"
                msg += "\n"
            await status_msg.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Cu phap: /git branch <owner/repo> <new_branch>", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    new_branch = context.args[2]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text(f"⏳ Dang tao branch...\n🌿 `{new_branch}`", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.create_branch(owner, repo, new_branch)
        if success:
            await status_msg.edit_text(f"✅ Branch da tao!\n\n🌿 `{new_branch}`\n📦 `{repo_path}`", parse_mode=ParseMode.MARKDOWN)
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_pr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 5:
        await update.message.reply_text("❌ Cu phap: /git pr <owner/repo> <title> <head> <base>", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    title = context.args[2]
    head = context.args[3]
    base = context.args[4]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text("⏳ Dang tao Pull Request...", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.create_pr(owner, repo, title, head, base)
        if success:
            pr_url = data.get("html_url", "") if isinstance(data, dict) else ""
            pr_num = data.get("number", "") if isinstance(data, dict) else ""
            await status_msg.edit_text(
                f"✅ Pull Request da tao!\n\n🔢 #{pr_num}\n📝 Title: `{title}`\n🌿 `{head}` → `{base}`\n🔗 {pr_url}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Cu phap: /git delete <owner/repo> <path>", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    file_path = context.args[2]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text(f"⏳ Dang xoa file...\n🗑 `{file_path}`", parse_mode=ParseMode.MARKDOWN)
    try:
        success_get, data_get = await github_agent.get_file(owner, repo, file_path)
        if not success_get:
            await status_msg.edit_text(f"❌ Khong tim thay file: `{file_path}`", parse_mode=ParseMode.MARKDOWN)
            return
        sha = data_get.get("sha", "") if isinstance(data_get, dict) else ""
        success, data = await github_agent.delete_file(owner, repo, file_path, f"chore: delete {file_path} via Denia Bot", sha)
        if success:
            await status_msg.edit_text(f"✅ Da xoa file!\n\n🗑 `{file_path}`\n📦 `{repo_path}`", parse_mode=ParseMode.MARKDOWN)
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_commits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Cu phap: /git commits <owner/repo>", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text("⏳ Dang lay lich su commits...", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.get_commits(owner, repo)
        if success and isinstance(data, list):
            msg = f"📝 Commit History — `{repo_path}`\n{'━' * 22}\n\n"
            for i, commit in enumerate(data[:10], 1):
                sha = commit.get("sha", "")[:7]
                message = commit.get("commit", {}).get("message", "")[:50]
                author = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
                date = commit.get("commit", {}).get("author", {}).get("date", "")[:10]
                msg += f"{i}. `{sha}` — {message}...\n   👤 {author} 📅 {date}\n\n"
            await status_msg.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Cu phap: /git update <owner/repo> <path> (reply code)", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    file_path = context.args[2]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    content = ""
    if update.message.reply_to_message and update.message.reply_to_message.text:
        content = update.message.reply_to_message.text
    elif len(context.args) > 3:
        content = " ".join(context.args[3:])
    if not content:
        await update.message.reply_text("❌ Thieu noi dung! Reply code de update.", parse_mode=ParseMode.MARKDOWN)
        return
    status_msg = await update.message.reply_text(f"⏳ Dang update file...\n📝 `{file_path}`", parse_mode=ParseMode.MARKDOWN)
    try:
        success_get, data_get = await github_agent.get_file(owner, repo, file_path)
        if not success_get:
            await status_msg.edit_text(f"❌ File khong ton tai: `{file_path}`\nDung /git push de tao moi.", parse_mode=ParseMode.MARKDOWN)
            return
        sha = data_get.get("sha", "") if isinstance(data_get, dict) else ""
        success, data = await github_agent.update_file(owner, repo, file_path, content, f"fix: update {file_path} via Denia Bot", sha)
        if success:
            await status_msg.edit_text(
                f"✅ Da update file!\n\n📝 `{file_path}`\n📦 `{repo_path}`\n📊 Size: `{len(content)}` chars",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Cu phap: /git issue <owner/repo> <title> [body]", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    title = context.args[2]
    body = " ".join(context.args[3:]) if len(context.args) > 3 else "Created via Denia Bot"
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text("⏳ Dang tao issue...", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.create_issue(owner, repo, title, body)
        if success:
            issue_url = data.get("html_url", "") if isinstance(data, dict) else ""
            issue_num = data.get("number", "") if isinstance(data, dict) else ""
            await status_msg.edit_text(
                f"✅ Issue da tao!\n\n🔢 #{issue_num}\n📝 `{title}`\n🔗 {issue_url}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_release(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Cu phap: /git release <owner/repo> <tag> [name]", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    tag = context.args[2]
    name = " ".join(context.args[3:]) if len(context.args) > 3 else f"Release {tag}"
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text(f"⏳ Dang tao release {tag}...", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.create_release(owner, repo, tag, name)
        if success:
            release_url = data.get("html_url", "") if isinstance(data, dict) else ""
            await status_msg.edit_text(
                f"🎉 Release da tao!\n\n🏷 `{tag}`\n📝 `{name}`\n🔗 {release_url}",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Cu phap: /git workflow <owner/repo> <name>\nTao workflow CI mau. Dung /cicd de tao custom.", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    name = context.args[2]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    workflow_content = generate_github_actions("python")
    status_msg = await update.message.reply_text("⏳ Dang tao workflow...", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.create_workflow(owner, repo, name, workflow_content)
        if success:
            await status_msg.edit_text(
                f"✅ Workflow da tao!\n\n⚙️ `.github/workflows/{name}.yml`\n📦 `{repo_path}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Cu phap: /git search <query>", parse_mode=ParseMode.MARKDOWN)
        return
    query = " ".join(context.args[1:])
    status_msg = await update.message.reply_text(f"🔍 Dang tim: `{query}`...", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.search_repos(query)
        if success:
            msg = f"🔍 Ket Qua Tim Kiem\n{'━' * 22}\n\n"
            for i, repo in enumerate(data[:10], 1):
                name = repo.get("full_name", "")
                desc = repo.get("description", "") or "Khong co mo ta"
                stars = repo.get("stargazers_count", 0)
                lang = repo.get("language", "Unknown")
                msg += f"{i}. ⭐ `{stars}` | `{name}`\n   📝 {desc[:60]}...\n   🔤 {lang}\n\n"
            await status_msg.edit_text(msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await status_msg.edit_text("❌ Khong tim thay ket qua.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_fork(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Cu phap: /git fork <owner/repo>", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    status_msg = await update.message.reply_text(f"⏳ Dang fork {repo_path}...", parse_mode=ParseMode.MARKDOWN)
    try:
        success, data = await github_agent.fork_repo(owner, repo)
        if success:
            fork_url = data.get("html_url", "") if isinstance(data, dict) else ""
            await status_msg.edit_text(f"✅ Da fork!\n\n📦 `{repo_path}`\n🔗 {fork_url}", parse_mode=ParseMode.MARKDOWN)
        else:
            error = data.get("message", str(data)) if isinstance(data, dict) else str(data)
            await status_msg.edit_text(f"❌ Loi:\n`{error[:400]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_star(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Cu phap: /git star <owner/repo>", parse_mode=ParseMode.MARKDOWN)
        return
    repo_path = context.args[1]
    if "/" not in repo_path:
        await update.message.reply_text("❌ Format: owner/repo", parse_mode=ParseMode.MARKDOWN)
        return
    owner, repo = repo_path.split("/", 1)
    try:
        success, _ = await github_agent.star_repo(owner, repo)
        if success:
            await update.message.reply_text(f"⭐ Da star: `{repo_path}`", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ Khong the star repo.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

async def _git_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        success, data = await github_agent.get_rate_limit()
        if success and isinstance(data, dict):
            core = data.get("resources", {}).get("core", {})
            remaining = core.get("remaining", 0)
            limit = core.get("limit", 0)
            reset_time = core.get("reset", 0)
            reset_dt = datetime.fromtimestamp(reset_time).strftime("%H:%M:%S") if reset_time else "Unknown"
            await update.message.reply_text(
                f"📊 GitHub Rate Limit\n"
                f"{'━' * 20}\n\n"
                f"• Con lai: `{remaining}/{limit}`\n"
                f"• Reset luc: `{reset_dt}`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Khong lay duoc rate limit.", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Loi: `{str(e)[:400]}`", parse_mode=ParseMode.MARKDOWN)

# ============================ AGENT COMMANDS (WITH MODEL SELECTION) ============================

async def agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)

    if not context.args:
        await update.message.reply_text(
            "🤖 Agent Mode — Tu dong code & push GitHub\n"
            f"{'━' * 26}\n\n"
            "Cach dung:\n"
            "/agent <mo ta cong viec>\n\n"
            "Vi du:\n"
            "• /agent Tao REST API FastAPI CRUD users\n"
            "• /agent Viet bot Telegram python-telegram-bot\n"
            "• /agent Tao script crawl Wikipedia\n\n"
            "⚠️ Truoc khi chay, ban se duoc chon model AI va xem canh bao chi phi.\n"
            "💡 Agent se tu dong: Phan tich → Code → Review → Test → Push → Bao cao",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    task_description = " ".join(context.args)

    # STEP 1: Show model selection with cost warnings
    models_list = MODE_CONFIG["agent"]["models"]
    keyboard = []
    row = []

    for idx, (cat, model_id, display, tier, inp, out) in enumerate(models_list[:20], 1):  # Show top 20
        cost_warn = get_model_cost_warning(model_id)
        btn_text = f"{idx}.{display[:18]}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"agent_model_{idx}_{task_description[:50]}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("❌ Huy", callback_data="agent_cancel")])

    state.pending_agent_task = task_description
    _save_state()

    await update.message.reply_text(
        f"🤖 Agent Task: *{task_description[:80]}*...\n"
        f"{'━' * 24}\n\n"
        f"📊 Model hien tai: `{state.current_model}`\n"
        f"💰 Canh bao: {get_model_cost_warning(state.current_model)}\n\n"
        f"👇 Chon model AI cho task nay (hoac dung model hien tai):\n"
        f"⚠️ Model dat tien co the ton nhieu chi phi!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def agent_model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    data = query.data

    if data == "agent_cancel":
        state.pending_agent_task = None
        state.pending_agent_model = None
        _save_state()
        await query.edit_message_text("❌ Agent task da bi huy.")
        return

    if data.startswith("agent_model_"):
        parts = data.split("_")
        try:
            choice = int(parts[2])
            models_list = MODE_CONFIG["agent"]["models"]
            if 1 <= choice <= len(models_list):
                cat, selected_id, selected_disp, tier, inp, out = models_list[choice - 1]
                state.pending_agent_model = selected_id
                _save_state()

                cost_warn = get_model_cost_warning(selected_id)
                budget_warn = check_budget_warning(state, estimated_cost=5000)

                confirm_text = (
                    f"🤖 Xac Nhan Agent Task\n"
                    f"{'━' * 24}\n\n"
                    f"📝 Task: `{state.pending_agent_task[:80]}...`\n"
                    f"🤖 Model: *{selected_id}*\n"
                    f"💰 {cost_warn}\n"
                )
                if budget_warn:
                    confirm_text += f"\n🚨 {budget_warn}\n"

                confirm_text += "\n👇 Xac nhan de bat dau:"

                keyboard = [
                    [InlineKeyboardButton("✅ Bat dau", callback_data="agent_confirm")],
                    [InlineKeyboardButton("❌ Huy", callback_data="agent_cancel")],
                ]
                await query.edit_message_text(confirm_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.edit_message_text("❌ So khong hop le.", parse_mode=ParseMode.MARKDOWN)
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Loi xu ly.", parse_mode=ParseMode.MARKDOWN)
    elif data == "agent_confirm":
        await query.edit_message_text("🚀 Dang khoi dong Agent...")
        await _run_agent_task(update, context, state)

async def _run_agent_task(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState):
    task_description = state.pending_agent_task
    model_id = state.pending_agent_model or state.current_model

    if not task_description:
        await update.effective_message.reply_text("❌ Khong tim thay task. Vui long dung /agent lai.", parse_mode=ParseMode.MARKDOWN)
        return

    task_id = generate_task_id()
    task = AgentTask(
        task_id=task_id,
        description=task_description,
        selected_model=model_id,
        status="running"
    )
    state.agent_tasks.append(task)
    state.pending_agent_task = None
    state.pending_agent_model = None
    _save_state()

    status_msg = await update.effective_message.reply_text(
        f"🤖 Agent Task Bat Dau\n"
        f"{'━' * 24}\n\n"
        f"🆔 Task ID: `{task_id}`\n"
        f"📝 Mo ta: {task_description[:100]}...\n"
        f"🤖 Model: `{model_id}`\n\n"
        f"⏳ Buoc 1/5: 📋 Phan tich yeu cau...\n"
        f"`{build_progress_bar(1, 5)}`",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        session = context.bot_data.get('session')
        if not session:
            session = aiohttp.ClientSession()
            context.bot_data['session'] = session

        # Step 1: Plan
        task.status = "planning"
        plan_messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Task: {task_description}\n\n"
                f"Hay lap ke hoach chi tiet:\n"
                f"1. Files can tao\n"
                f"2. Cau truc project\n"
                f"3. Dependencies\n"
                f"4. Cac buoc implement\n\n"
                f"Tra loi ngan gon, bullet points."
            )}
        ]
        plan_text, plan_metrics = await call_chat_api(
            session, model_id, plan_messages, status_msg,
            system_prompt=AGENT_SYSTEM_PROMPT, max_tokens=2048
        )
        task.plan = plan_text
        task.cost_vnd += estimate_cost(model_id, plan_metrics['input_tokens'], plan_metrics['output_tokens'])

        # Step 2: Generate code
        task.status = "coding"
        await status_msg.edit_text(
            f"🤖 Agent Task Dang Chay\n"
            f"{'━' * 24}\n\n"
            f"🆔 `{task_id}`\n"
            f"🤖 Model: `{model_id}`\n"
            f"⏳ Buoc 2/5: 💻 Viet code hoan chinh...\n"
            f"`{build_progress_bar(2, 5)}`",
            parse_mode=ParseMode.MARKDOWN
        )

        code_messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Task: {task_description}\n\n"
                f"Ke hoach:\n{plan_text}\n\n"
                f"Hay viet code HOAN CHINH, day du, co the chay duoc ngay.\n"
                f"Bao gom tat ca file, docstrings, error handling, requirements.txt, README.md.\n"
                f"Format: Moi file bat dau bang `===FILENAME===`"
            )}
        ]
        code_text, code_metrics = await call_chat_api(
            session, model_id, code_messages, status_msg,
            system_prompt=AGENT_SYSTEM_PROMPT, max_tokens=MAX_OUTPUT_TOKENS
        )
        task.cost_vnd += estimate_cost(model_id, code_metrics['input_tokens'], code_metrics['output_tokens'])

        # Step 3: Syntax & Security check
        task.status = "reviewing"
        await status_msg.edit_text(
            f"🤖 Agent Task Dang Chay\n"
            f"{'━' * 24}\n\n"
            f"🆔 `{task_id}`\n"
            f"🤖 Model: `{model_id}`\n"
            f"⏳ Buoc 3/5: 🔍 Kiem tra syntax & security...\n"
            f"`{build_progress_bar(3, 5)}`",
            parse_mode=ParseMode.MARKDOWN
        )

        files = {}
        current_file = None
        current_content = []
        for line in code_text.split('\n'):
            if line.startswith('===') and line.endswith('==='):
                if current_file and current_content:
                    files[current_file] = '\n'.join(current_content)
                current_file = line.replace('===', '').strip()
                current_content = []
            elif current_file is not None:
                current_content.append(line)
        if current_file and current_content:
            files[current_file] = '\n'.join(current_content)
        if not files:
            files = {"main.py": code_text}

        syntax_issues = []
        security_issues = []
        for fname, fcontent in files.items():
            if fname.endswith('.py'):
                try:
                    compile(fcontent, fname, 'exec')
                except SyntaxError as e:
                    syntax_issues.append(f"❌ {fname}: Line {e.lineno}: {e.msg}")
                analysis = await agent_analyze_code(fcontent)
                security_issues.extend(analysis["issues"])

        # Auto-fix if issues found
        if syntax_issues:
            await status_msg.edit_text(
                f"🤖 Agent Task Dang Chay\n"
                f"{'━' * 24}\n\n"
                f"🆔 `{task_id}`\n"
                f"⚠️ Phat hien loi:\n"
                f"{'\n'.join(syntax_issues[:3])}\n\n"
                f"⏳ Buoc 3.5/5: 🔧 Tu dong sua loi...",
                parse_mode=ParseMode.MARKDOWN
            )
            fix_messages = [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Code co loi:\n"
                    f"{'\n'.join(syntax_issues)}\n\n"
                    f"Hay sua lai. Giu format `===FILENAME===`. Chi tra code."
                )}
            ]
            fixed_code, _ = await call_chat_api(
                session, model_id, fix_messages, status_msg,
                system_prompt=AGENT_SYSTEM_PROMPT, max_tokens=MAX_OUTPUT_TOKENS
            )
            files = {}
            current_file = None
            current_content = []
            for line in fixed_code.split('\n'):
                if line.startswith('===') and line.endswith('==='):
                    if current_file and current_content:
                        files[current_file] = '\n'.join(current_content)
                    current_file = line.replace('===', '').strip()
                    current_content = []
                elif current_file is not None:
                    current_content.append(line)
            if current_file and current_content:
                files[current_file] = '\n'.join(current_content)
            if not files:
                files = {"main.py": fixed_code}

        # Step 4: Push to GitHub
        task.status = "pushing"
        await status_msg.edit_text(
            f"🤖 Agent Task Dang Chay\n"
            f"{'━' * 24}\n\n"
            f"🆔 `{task_id}`\n"
            f"🤖 Model: `{model_id}`\n"
            f"⏳ Buoc 4/5: 🚀 Push len GitHub...\n"
            f"`{build_progress_bar(4, 5)}`",
            parse_mode=ParseMode.MARKDOWN
        )

        success_user, user_data = await github_agent.get_user()
        if not success_user:
            raise Exception("Khong the xac thuc GitHub token")

        github_username = user_data.get("login", "")
        state.github_username = github_username

        repo_name = sanitize_repo_name(task_description[:40])
        repo_name = repo_name or f"denia-agent-{task_id[:8]}"

        success_repo, repo_data = await github_agent.create_repo(
            repo_name, f"Auto-generated by Denia Bot: {task_description[:100]}"
        )
        if not success_repo:
            repo_name = f"{repo_name}-{task_id[:6]}"
            success_repo, repo_data = await github_agent.create_repo(
                repo_name, f"Auto-generated by Denia Bot: {task_description[:100]}"
            )

        repo_full = f"{github_username}/{repo_name}"
        task.repo_url = f"https://github.com/{repo_full}"

        pushed_files = []
        for fname, fcontent in files.items():
            success_push, _ = await github_agent.create_file(
                github_username, repo_name, fname, fcontent,
                f"feat: add {fname} via Denia Bot"
            )
            if success_push:
                pushed_files.append(fname)
            await asyncio.sleep(0.5)

        # Step 5: Report
        task.status = "completed"
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.files_created = pushed_files
        state.stats.tasks_completed += 1

        reflection = await agent_self_reflect(task, state)

        total_latency = plan_metrics['latency'] + code_metrics['latency']
        total_input = plan_metrics['input_tokens'] + code_metrics['input_tokens']
        total_output = plan_metrics['output_tokens'] + code_metrics['output_tokens']

        result_msg = (
            f"✅ Agent Task Hoan Thanh!\n"
            f"{'━' * 24}\n\n"
            f"🆔 Task ID: `{task_id}`\n"
            f"📝 Mo ta: {task_description[:80]}...\n"
            f"🤖 Model: `{model_id}`\n\n"
            f"📦 Repository:\n"
            f"🔗 [{repo_full}](https://github.com/{repo_full})\n\n"
            f"📁 Files da push ({len(pushed_files)}):\n"
            f"{'\n'.join([f'• `{f}`' for f in pushed_files])}\n\n"
            f"🔍 Syntax Check:\n"
            f"{'✅ Tat ca file hop le' if not syntax_issues else '\n'.join(syntax_issues[:3])}\n\n"
            f"🛡 Security:\n"
            f"{'✅ Khong phat hien lo hong' if not security_issues else '\n'.join(security_issues[:3])}\n\n"
            f"📊 AI Metrics:\n"
            f"• ⏱ Latency: `{total_latency:.2f}s`\n"
            f"• 📝 Input: `{total_input}` tok\n"
            f"• 💬 Output: `{total_output}` tok\n"
            f"• 💰 Cost: `{format_vnd(task.cost_vnd)}` VND\n\n"
            f"{reflection}"
        )

        await status_msg.edit_text(result_msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False)

        full_code_text = f"# {task_description}\n# Repo: https://github.com/{repo_full}\n\n"
        for fname, fcontent in files.items():
            full_code_text += f"\n{'='*60}\n# FILE: {fname}\n{'='*60}\n\n{fcontent}\n"

        bio = io.BytesIO(full_code_text.encode('utf-8'))
        bio.name = f"agent_{task_id[:8]}_code.txt"
        await update.effective_message.reply_document(
            document=bio,
            caption=f"📄 Full source — {len(files)} files | 💰 {format_vnd(task.cost_vnd)} VND"
        )

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state.stats.tasks_failed += 1
        _save_state()

        await status_msg.edit_text(
            f"❌ Agent Task That Bai\n"
            f"{'━' * 24}\n\n"
            f"🆔 `{task_id}`\n"
            f"🤖 Model: `{model_id}`\n"
            f"⚠️ Loi: `{str(e)[:300]}`\n\n"
            f"💡 Thu:\n"
            f"• Kiem tra GitHub token\n"
            f"• Don gian hoa yeu cau\n"
            f"• Thu lai voi /agent\n\n"
            f"🧠 AI da ghi nhan loi.",
            parse_mode=ParseMode.MARKDOWN
        )
        await agent_self_reflect(task, state)

async def agent_advanced_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = await get_user_state(user_id)

    if not context.args:
        await update.message.reply_text(
            "🤖 Advanced Agent\n"
            f"{'━' * 22}\n\n"
            "Giong /agent nhung co them:\n"
            "• 🔍 Code review tu dong\n"
            "• 🧪 Unit test generation\n"
            "• 📚 Auto-documentation\n"
            "• 🐳 Dockerfile generation\n"
            "• ⚙️ CI/CD workflow\n\n"
            "Cu phap: /agent_advanced <mo ta>\n"
            "⚠️ Se duoc chon model va xem canh bao chi phi truoc.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    task_description = " ".join(context.args)

    # Show model selection
    models_list = MODE_CONFIG["agent"]["models"]
    keyboard = []
    row = []
    for idx, (cat, model_id, display, tier, inp, out) in enumerate(models_list[:15], 1):
        btn_text = f"{idx}.{display[:18]}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"advagent_model_{idx}_{task_description[:50]}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Huy", callback_data="advagent_cancel")])

    state.pending_agent_task = task_description
    _save_state()

    await update.message.reply_text(
        f"🤖 Advanced Agent: *{task_description[:80]}*...\n"
        f"{'━' * 24}\n\n"
        f"📊 Model hien tai: `{state.current_model}`\n"
        f"💰 {get_model_cost_warning(state.current_model)}\n\n"
        f"👇 Chon model AI (10 buoc, ton nhieu token):",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def advagent_model_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    state = await get_user_state(user_id)
    data = query.data

    if data == "advagent_cancel":
        state.pending_agent_task = None
        state.pending_agent_model = None
        _save_state()
        await query.edit_message_text("❌ Advanced Agent da bi huy.")
        return

    if data.startswith("advagent_model_"):
        parts = data.split("_")
        try:
            choice = int(parts[2])
            models_list = MODE_CONFIG["agent"]["models"]
            if 1 <= choice <= len(models_list):
                cat, selected_id, selected_disp, tier, inp, out = models_list[choice - 1]
                state.pending_agent_model = selected_id
                _save_state()

                cost_warn = get_model_cost_warning(selected_id)
                budget_warn = check_budget_warning(state, estimated_cost=10000)

                confirm_text = (
                    f"🤖 Xac Nhan Advanced Agent\n"
                    f"{'━' * 24}\n\n"
                    f"📝 Task: `{state.pending_agent_task[:80]}...`\n"
                    f"🤖 Model: *{selected_id}*\n"
                    f"💰 {cost_warn}\n"
                    f"⚠️ Advanced Agent co the ton nhieu chi phi!\n"
                )
                if budget_warn:
                    confirm_text += f"\n🚨 {budget_warn}\n"

                confirm_text += "\n👇 Xac nhan:"

                keyboard = [
                    [InlineKeyboardButton("✅ Bat dau (10 buoc)", callback_data="advagent_confirm")],
                    [InlineKeyboardButton("❌ Huy", callback_data="advagent_cancel")],
                ]
                await query.edit_message_text(confirm_text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.edit_message_text("❌ So khong hop le.", parse_mode=ParseMode.MARKDOWN)
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Loi xu ly.", parse_mode=ParseMode.MARKDOWN)
    elif data == "advagent_confirm":
        await query.edit_message_text("🚀 Dang khoi dong Advanced Agent...")
        await _run_advanced_agent(update, context, state)

async def _run_advanced_agent(update: Update, context: ContextTypes.DEFAULT_TYPE, state: ConversationState):
    task_description = state.pending_agent_task
    model_id = state.pending_agent_model or state.current_model

    if not task_description:
        await update.effective_message.reply_text("❌ Khong tim thay task.", parse_mode=ParseMode.MARKDOWN)
        return

    task_id = generate_task_id()
    task = AgentTask(task_id=task_id, description=task_description, selected_model=model_id, status="running")
    state.agent_tasks.append(task)
    state.pending_agent_task = None
    state.pending_agent_model = None
    _save_state()

    status_msg = await update.effective_message.reply_text(
        f"🤖 Advanced Agent — 10 buoc\n"
        f"{'━' * 24}\n"
        f"🆔 `{task_id}`\n"
        f"🤖 Model: `{model_id}`\n"
        f"⏳ Bat dau...",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        session = context.bot_data.get('session')
        if not session:
            session = aiohttp.ClientSession()
            context.bot_data['session'] = session

        steps = [
            ("📋 Phan tich", "plan"), ("💻 Viet code", "code"), ("🔍 Self-review", "review"),
            ("🧪 Tao tests", "test"), ("🛡 Security scan", "security"), ("📚 Viet docs", "docs"),
            ("🐳 Tao Dockerfile", "docker"), ("⚙️ Tao CI/CD", "cicd"), ("🚀 Push GitHub", "push"),
            ("✅ Verify", "verify")
        ]

        for i, (label, key) in enumerate(steps[:2], 1):
            await status_msg.edit_text(
                f"🤖 Advanced Agent\n"
                f"{'━' * 24}\n"
                f"🆔 `{task_id}`\n"
                f"🤖 Model: `{model_id}`\n"
                f"⏳ Buoc {i}/10: {label}...\n"
                f"`{build_progress_bar(i, 10)}`",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1)

        code_messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Task: {task_description}\n\n"
                f"Viet code hoan chinh + README + requirements.txt.\n"
                f"Format: `===FILENAME===`"
            )}
        ]
        code_text, _ = await call_chat_api(session, model_id, code_messages, status_msg, max_tokens=MAX_OUTPUT_TOKENS)

        files = {}
        current_file = None
        current_content = []
        for line in code_text.split('\n'):
            if line.startswith('===') and line.endswith('==='):
                if current_file and current_content:
                    files[current_file] = '\n'.join(current_content)
                current_file = line.replace('===', '').strip()
                current_content = []
            elif current_file is not None:
                current_content.append(line)
        if current_file and current_content:
            files[current_file] = '\n'.join(current_content)
        if not files:
            files = {"main.py": code_text}

        await status_msg.edit_text(
            f"🤖 Advanced Agent\n"
            f"{'━' * 24}\n"
            f"🆔 `{task_id}`\n"
            f"🤖 Model: `{model_id}`\n"
            f"⏳ Buoc 3/10: 🔍 Self-review...",
            parse_mode=ParseMode.MARKDOWN
        )

        review_messages = [
            {"role": "system", "content": "Ban la senior code reviewer. Review code sau va dua ra nhan xet chi tiet."},
            {"role": "user", "content": f"Review code:\n\n```python\n{files.get('main.py', list(files.values())[0])[:3000]}\n```"}
        ]
        review_text, _ = await call_chat_api(session, model_id, review_messages, status_msg, max_tokens=2048)
        task.code_review = review_text

        await status_msg.edit_text(
            f"🤖 Advanced Agent\n"
            f"{'━' * 24}\n"
            f"🆔 `{task_id}`\n"
            f"🤖 Model: `{model_id}`\n"
            f"⏳ Buoc 4/10: 🧪 Tao unit tests...",
            parse_mode=ParseMode.MARKDOWN
        )

        test_messages = [
            {"role": "system", "content": "Viet pytest unit tests day du. Chi tra code."},
            {"role": "user", "content": f"Code:\n```python\n{files.get('main.py', list(files.values())[0])[:2000]}\n```"}
        ]
        test_code, _ = await call_chat_api(session, model_id, test_messages, status_msg, max_tokens=2048)
        files["test_main.py"] = test_code.replace("```python", "").replace("```", "")

        for i, (label, key) in enumerate(steps[4:6], 5):
            await status_msg.edit_text(
                f"🤖 Advanced Agent\n"
                f"{'━' * 24}\n"
                f"🆔 `{task_id}`\n"
                f"🤖 Model: `{model_id}`\n"
                f"⏳ Buoc {i}/10: {label}...",
                parse_mode=ParseMode.MARKDOWN
            )

        files["Dockerfile"] = generate_dockerfile("python")
        files[".github/workflows/ci.yml"] = generate_github_actions("python")

        await status_msg.edit_text(
            f"🤖 Advanced Agent\n"
            f"{'━' * 24}\n"
            f"🆔 `{task_id}`\n"
            f"🤖 Model: `{model_id}`\n"
            f"⏳ Buoc 9/10: 🚀 Push GitHub...",
            parse_mode=ParseMode.MARKDOWN
        )

        success_user, user_data = await github_agent.get_user()
        github_username = user_data.get("login", "")
        repo_name = sanitize_repo_name(task_description[:40]) or f"denia-adv-{task_id[:6]}"
        await github_agent.create_repo(repo_name, f"Advanced project by Denia Bot: {task_description[:100]}")

        pushed_files = []
        for fname, fcontent in files.items():
            success, _ = await github_agent.create_file(github_username, repo_name, fname, fcontent, f"feat: add {fname}")
            if success:
                pushed_files.append(fname)
            await asyncio.sleep(0.5)

        task.status = "completed"
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task.files_created = pushed_files
        state.stats.tasks_completed += 1
        _save_state()

        result_msg = (
            f"✅ Advanced Agent Hoan Thanh!\n"
            f"{'━' * 24}\n\n"
            f"🆔 `{task_id}`\n"
            f"🤖 Model: `{model_id}`\n"
            f"📦 `{github_username}/{repo_name}`\n"
            f"🔗 https://github.com/{github_username}/{repo_name}\n\n"
            f"📁 Files ({len(pushed_files)}):\n"
            f"{'\n'.join([f'• `{f}`' for f in pushed_files])}\n\n"
            f"🔍 Review:\n```\n{review_text[:500]}\n```"
        )
        await status_msg.edit_text(result_msg, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        state.stats.tasks_failed += 1
        _save_state()
        await status_msg.edit_text(f"❌ Loi: `{str(e)[:300]}`", parse_mode=ParseMode.MARKDOWN)

# ============================ MAIN MESSAGE HANDLER ============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    state = await get_user_state(user_id)
    if not user_input:
        return

    mode = state.mode
    model_id = state.current_model
    mode_name = MODE_CONFIG[mode]["name"]

    valid_models = [m[1] for m in MODE_CONFIG[mode]["models"]]
    if model_id not in valid_models:
        model_id = MODE_CONFIG[mode]["default"]
        state.current_model = model_id

    # Check budget before processing
    budget_warn = check_budget_warning(state)
    if budget_warn and "vuot qua" in budget_warn:
        await update.message.reply_text(
            f"🚨 {budget_warn}\n\n"
            f"Dung /settings budget 0 de bo gioi han hoac nap them.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Auto-summarize if history too long
    await auto_summarize_history(state)

    status_msg = await update.message.reply_text(
        f"⏳ Dang khoi tao...\n"
        f"🔄 Mode: {mode_name}\n"
        f"🤖 Model: `{model_id}`",
        parse_mode=ParseMode.MARKDOWN
    )

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    session = context.bot_data.get('session')
    if not session:
        session = aiohttp.ClientSession()
        context.bot_data['session'] = session

    try:
        if mode == "chat":
            await _handle_chat(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "agent":
            await _handle_agent_chat(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "coder":
            await _handle_coder_chat(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "lesson":
            await _handle_lesson_chat(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "embed":
            await _handle_embed(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "tts":
            await _handle_tts(update, context, state, model_id, user_input, status_msg, session)
        elif mode == "vision":
            await _handle_vision_chat(update, context, state, model_id, user_input, status_msg, session)
    except Exception as e:
        logger.error(f"Error: {e}")
        error_msg = (
            f"⚠️ Loi xu ly\n"
            f"{'━' * 15}\n"
            f"`{str(e)[:400]}`\n\n"
            f"💡 Thu: /reset hoac doi model/mode"
        )
        try:
            await status_msg.edit_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)
        state.last_error = str(e)
        state.self_notes.append(f"Error in {mode} mode: {str(e)[:200]}")
        _save_state()

async def _handle_chat(update, context, state, model_id, user_input, status_msg, session):
    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]
    branch = state.branches.get(state.current_branch_id)
    if branch:
        branch.messages = state.history.copy()

    system = SYSTEM_PROMPT
    persona_notes = [n for n in state.self_notes if n.startswith("Persona:")]
    if persona_notes:
        system += f"\n\nPersona: {persona_notes[-1].replace('Persona: ', '')}"
    if state.context_summary:
        system += f"\n\nContext Summary: {state.context_summary}"

    messages = [{"role": "system", "content": system}] + state.history
    ai_response, metrics = await call_chat_api(session, model_id, messages, status_msg, system_prompt=system)

    state.history.append({"role": "assistant", "content": ai_response})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]
    if branch:
        branch.messages = state.history.copy()

    model_disp = get_model_display("chat", model_id)
    header = f"🤖 {model_disp}\n{'━' * 20}\n\n"
    footer = build_metrics_footer(metrics, state, model_id)
    full_text = header + ai_response + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    await send_long_text(update, full_text, filename="ai_response.txt")
    _save_state()

async def _handle_agent_chat(update, context, state, model_id, user_input, status_msg, session):
    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]
    branch = state.branches.get(state.current_branch_id)
    if branch:
        branch.messages = state.history.copy()

    agent_context = AGENT_SYSTEM_PROMPT
    if state.github_username:
        agent_context += f"\n\nGitHub user: {state.github_username}"
    if state.self_notes:
        agent_context += f"\n\nLessons learned:\n" + "\n".join(state.self_notes[-5:])
    if state.context_summary:
        agent_context += f"\n\nContext Summary: {state.context_summary}"

    messages = [{"role": "system", "content": agent_context}] + state.history
    ai_response, metrics = await call_chat_api(
        session, model_id, messages, status_msg,
        system_prompt=agent_context, max_tokens=MAX_OUTPUT_TOKENS
    )

    state.history.append({"role": "assistant", "content": ai_response})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]
    if branch:
        branch.messages = state.history.copy()

    model_disp = get_model_display("agent", model_id)
    header = f"🤖 {model_disp} [AGENT MODE]\n{'━' * 20}\n\n"
    footer = build_metrics_footer(metrics, state, model_id)
    full_text = header + ai_response + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    await send_long_text(update, full_text, filename="agent_response.txt")
    _save_state()

async def _handle_coder_chat(update, context, state, model_id, user_input, status_msg, session):
    coder_prompt = (
        "You are Denia Bot in CODER MODE. You are an expert software engineer.\n"
        "Rules:\n"
        "1. Always provide complete, runnable code\n"
        "2. Include error handling and edge cases\n"
        "3. Use best practices and design patterns\n"
        "4. Explain complex logic with comments\n"
        "5. Suggest optimizations when possible"
    )
    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    messages = [{"role": "system", "content": coder_prompt}] + state.history
    ai_response, metrics = await call_chat_api(
        session, model_id, messages, status_msg,
        system_prompt=coder_prompt, max_tokens=MAX_OUTPUT_TOKENS, temperature=0.3
    )

    state.history.append({"role": "assistant", "content": ai_response})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    model_disp = get_model_display("coder", model_id)
    header = f"💻 {model_disp} [CODER MODE]\n{'━' * 20}\n\n"
    footer = build_metrics_footer(metrics, state, model_id)
    full_text = header + ai_response + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    await send_long_text(update, full_text, filename="coder_response.txt")
    _save_state()

async def _handle_lesson_chat(update, context, state, model_id, user_input, status_msg, session):
    # In lesson mode, user can ask questions about programming
    lang = state.preferences.learning_language
    level = state.preferences.learning_level

    lesson_context = (
        f"You are Denia Bot in TEACHER MODE for {LANGUAGE_DISPLAY.get(lang, lang)}.\n"
        f"Student level: {level}.\n"
        f"Answer questions clearly, provide examples, and encourage learning.\n"
        f"Use Vietnamese for explanations, English for code."
    )

    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    messages = [{"role": "system", "content": lesson_context}] + state.history
    ai_response, metrics = await call_chat_api(
        session, model_id, messages, status_msg,
        system_prompt=lesson_context, max_tokens=MAX_OUTPUT_TOKENS, temperature=0.7
    )

    state.history.append({"role": "assistant", "content": ai_response})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    model_disp = get_model_display("lesson", model_id)
    header = f"📚 {model_disp} [LESSON MODE — {LANGUAGE_DISPLAY.get(lang, lang)}]\n{'━' * 20}\n\n"
    footer = build_metrics_footer(metrics, state, model_id)
    full_text = header + ai_response + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    await send_long_text(update, full_text, filename="lesson_response.md", format_hint="md")
    _save_state()

async def _handle_vision_chat(update, context, state, model_id, user_input, status_msg, session):
    vision_prompt = (
        "You are Denia Bot in VISION MODE. You can analyze and describe images in detail.\n"
        "When discussing images, be precise about visual elements, colors, composition, and context."
    )
    state.history.append({"role": "user", "content": user_input})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    messages = [{"role": "system", "content": vision_prompt}] + state.history
    ai_response, metrics = await call_chat_api(
        session, model_id, messages, status_msg,
        system_prompt=vision_prompt, max_tokens=4096
    )

    state.history.append({"role": "assistant", "content": ai_response})
    if len(state.history) > MAX_HISTORY * 2:
        state.history = state.history[-(MAX_HISTORY * 2):]

    model_disp = get_model_display("vision", model_id)
    header = f"👁 {model_disp} [VISION MODE]\n{'━' * 20}\n\n"
    footer = build_metrics_footer(metrics, state, model_id)
    full_text = header + ai_response + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    await send_long_text(update, full_text, filename="vision_response.txt")
    _save_state()

async def _handle_embed(update, context, state, model_id, user_input, status_msg, session):
    content, metrics, full_vector = await call_embed_api(session, model_id, user_input, status_msg)
    footer = build_metrics_footer(metrics, state, model_id)
    full_text = content + footer

    try:
        await status_msg.delete()
    except Exception:
        pass

    try:
        await update.message.reply_text(full_text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(full_text)

    vector_bio = io.BytesIO(full_vector.encode('utf-8'))
    vector_bio.name = f"embedding_{model_id.replace('/', '_')}.json"
    await update.message.reply_document(document=vector_bio, caption=f"📄 Full embedding vector")
    _save_state()

async def _handle_tts(update, context, state, model_id, user_input, status_msg, session):
    audio_bytes, metrics = await call_tts_api(session, model_id, user_input, status_msg)
    footer_metrics = build_metrics_footer(metrics, state, model_id)

    try:
        await status_msg.delete()
    except Exception:
        pass

    audio_bio = io.BytesIO(audio_bytes)
    audio_bio.name = f"tts_{model_id.replace('/', '_')}.mp3"

    model_disp = get_model_display("tts", model_id)
    caption = (
        f"🔊 Text-to-Speech\n"
        f"🤖 Model: {model_disp}\n"
        f"📝 Length: `{len(user_input)}` chars\n"
        f"📦 Size: `{len(audio_bytes)}` bytes"
    ) + footer_metrics

    await update.message.reply_voice(voice=audio_bio, caption=caption, parse_mode=ParseMode.MARKDOWN)
    _save_state()

# ============================ INLINE QUERY ============================

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = [
        InlineQueryResultArticle(
            id="1",
            title="🤖 Hoi Denia Bot",
            input_message_content=InputTextMessageContent(
                f"🤖 Cau hoi: `{query}`\n\n⏳ Dang cho phan hoi...",
                parse_mode=ParseMode.MARKDOWN
            ),
            description=f"Gui cau hoi: {query[:50]}..."
        )
    ]
    await update.inline_query.answer(results, cache_time=0)

# ============================ ERROR HANDLER ============================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_user:
        state = await get_user_state(update.effective_user.id)
        error_str = str(context.error)[:300]
        state.last_error = error_str
        state.self_notes.append(f"System error [{datetime.now().strftime('%H:%M')}]: {error_str}")
        _save_state()
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😵 Da xay ra loi khong mong muon!\n"
            "Vui long thu lai sau.\n\n"
            "💡 Thu: /reset hoac /help",
            parse_mode=ParseMode.MARKDOWN
        )

# ============================ MAIN ============================

async def post_init(application: Application):
    application.bot_data['session'] = aiohttp.ClientSession()
    await github_agent.init_session()
    _load_state()

    commands = [
        BotCommand("start", "Khoi dong bot"),
        BotCommand("help", "Huong dan day du"),
        BotCommand("models", "Chon model AI"),
        BotCommand("switch", "Doi model nhanh"),
        BotCommand("mode", "Doi che do"),
        BotCommand("agent", "Agent tu dong code"),
        BotCommand("agent_advanced", "Agent nang cao"),
        BotCommand("git", "GitHub commands"),
        BotCommand("lesson", "Hoc lap trinh"),
        BotCommand("lesson_lang", "Chon ngon ngu hoc"),
        BotCommand("leetcode", "Luyen LeetCode"),
        BotCommand("kb", "Knowledge Base"),
        BotCommand("analyze", "Phan tich code"),
        BotCommand("run", "Chay Python sandbox"),
        BotCommand("runplot", "Chay Python + Matplotlib"),
        BotCommand("docker", "Tao Dockerfile"),
        BotCommand("cicd", "Tao GitHub Actions"),
        BotCommand("diff", "So sanh code"),
        BotCommand("testgen", "Tao unit test"),
        BotCommand("format", "Format code Python"),
        BotCommand("search", "Tim kiem web"),
        BotCommand("fetch", "Lay noi dung web"),
        BotCommand("image", "Tao anh AI"),
        BotCommand("tts", "Text-to-Speech"),
        BotCommand("stt", "Speech-to-Text"),
        BotCommand("vision", "Phan tich anh"),
        BotCommand("snippet", "Quan ly snippets"),
        BotCommand("whiteboard", "Bang trang"),
        BotCommand("branch", "Quan ly nhanh chat"),
        BotCommand("remind", "Hen gio nhac nho"),
        BotCommand("persona", "Dat tinh cach AI"),
        BotCommand("settings", "Cai dat ca nhan"),
        BotCommand("export", "Xuat du lieu"),
        BotCommand("import", "Nhap du lieu"),
        BotCommand("status", "Trang thai & chi phi"),
        BotCommand("stats", "Thong ke chi tiet"),
        BotCommand("tasks", "Lich su agent tasks"),
        BotCommand("learn", "Ghi chu tu hoc"),
        BotCommand("reset", "Xoa ngu canh"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Denia Bot v6.0 initialized. Sessions created. Commands set. State loaded.")

async def post_shutdown(application: Application):
    session = application.bot_data.get('session')
    if session:
        await session.close()
    await github_agent.close()
    _save_state()
    logger.info("🛑 All sessions closed. State saved.")

def main():
    logger.info("🚀 Starting Denia Bot v6.0 Ultimate...")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)
        .build()
    )

    # Core commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('models', show_models))
    application.add_handler(CommandHandler('switch', switch_model_command))
    application.add_handler(CommandHandler('mode', mode_command))
    application.add_handler(CommandHandler('reset', reset_chat))
    application.add_handler(CommandHandler('status', status_command))
    application.add_handler(CommandHandler('stats', stats_command))

    # Agent commands
    application.add_handler(CommandHandler('agent', agent_command))
    application.add_handler(CommandHandler('agent_advanced', agent_advanced_command))
    application.add_handler(CommandHandler('git', git_command))
    application.add_handler(CommandHandler('analyze', analyze_command))
    application.add_handler(CommandHandler('run', run_command))
    application.add_handler(CommandHandler('runplot', runplot_command))
    application.add_handler(CommandHandler('docker', docker_command))
    application.add_handler(CommandHandler('cicd', cicd_command))
    application.add_handler(CommandHandler('diff', diff_command))
    application.add_handler(CommandHandler('testgen', testgen_command))
    application.add_handler(CommandHandler('format', format_command))

    # Learning commands
    application.add_handler(CommandHandler('lesson', lesson_command))
    application.add_handler(CommandHandler('lesson_lang', lesson_lang_command))
    application.add_handler(CommandHandler('leetcode', leetcode_command))

    # Web & multimedia
    application.add_handler(CommandHandler('search', search_command))
    application.add_handler(CommandHandler('fetch', fetch_command))
    application.add_handler(CommandHandler('image', image_command))
    application.add_handler(CommandHandler('tts', tts_command))
    application.add_handler(CommandHandler('stt', stt_command))
    application.add_handler(CommandHandler('vision', vision_command))

    # Knowledge & memory
    application.add_handler(CommandHandler('kb', kb_command))
    application.add_handler(CommandHandler('branch', branch_command))
    application.add_handler(CommandHandler('remind', remind_command))
    application.add_handler(CommandHandler('persona', persona_command))
    application.add_handler(CommandHandler('settings', settings_command))
    application.add_handler(CommandHandler('export', export_command))
    application.add_handler(CommandHandler('import', import_command))
    application.add_handler(CommandHandler('tasks', tasks_command))
    application.add_handler(CommandHandler('learn', learn_command))
    application.add_handler(CommandHandler('snippet', snippet_command))
    application.add_handler(CommandHandler('whiteboard', whiteboard_command))

    # Callbacks
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^model_"))
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^refresh_models"))
    application.add_handler(CallbackQueryHandler(model_callback, pattern="^filter_"))
    application.add_handler(CallbackQueryHandler(mode_callback, pattern="^setmode_"))
    application.add_handler(CallbackQueryHandler(lesson_callback, pattern="^lesson_"))
    application.add_handler(CallbackQueryHandler(leetcode_callback, pattern="^leetcode_"))
    application.add_handler(CallbackQueryHandler(agent_model_callback, pattern="^agent_model_"))
    application.add_handler(CallbackQueryHandler(agent_model_callback, pattern="^agent_confirm"))
    application.add_handler(CallbackQueryHandler(agent_model_callback, pattern="^agent_cancel"))
    application.add_handler(CallbackQueryHandler(advagent_model_callback, pattern="^advagent_"))

    # Inline
    application.add_handler(InlineQueryHandler(inline_query))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Errors
    application.add_error_handler(error_handler)

    # Run
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
