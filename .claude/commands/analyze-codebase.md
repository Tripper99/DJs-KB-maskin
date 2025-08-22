---
allowed-tools: LS, Read, Glob, Write, Bash(find:*), Bash(tree:*), Bash(wc:*), Bash(du:*)
description: Generate comprehensive analysis and documentation of Python desktop codebase
---

# Comprehensive Python Desktop Application Analysis

Use Claude's built-in tools to analyze this codebase and create comprehensive documentation.

Start by exploring the project structure using LS, Glob, and Read tools, then create a detailed analysis.

Your task is to analyze this Python desktop application codebase and create comprehensive documentation that includes:

## 1. Project Overview
- Application type and purpose
- Python version and major dependencies  
- GUI framework used
- Architecture pattern

## 2. Directory Structure Analysis
- Purpose of each major directory
- Key modules and their functions
- Interconnections between components

## 3. File-by-File Breakdown
Categorize all important files by their role in the application.

## 4. GUI Architecture Analysis  
- Main window structure
- Dialog flows and interactions
- Event handling patterns
- State management

## 5. Data Flow Analysis
- Input sources and processing pipeline
- Output generation
- Configuration flow

## 6. Architecture Deep Dive
- Overall application structure
- Design patterns used
- Module dependencies

## 7. Technology Stack
- All libraries and frameworks used
- Development and build tools

## 8. Visual Architecture Diagram
Create a comprehensive ASCII diagram showing the application structure.

## 9. Key Insights & Recommendations
Provide assessment and suggestions for:
- Code quality
- Performance optimization
- Security considerations
- Maintainability improvements

**Write all output to: docs/codebase_analysis.md**